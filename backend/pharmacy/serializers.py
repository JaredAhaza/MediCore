import re
import logging
from decimal import Decimal
from django.db import transaction as db_transaction
from rest_framework import serializers
from .models import Medicine, InventoryTransaction, PrescriptionDispense
from emr.models import Prescription


# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MedicineSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'category', 'manufacturer',
            'description', 'current_stock', 'reorder_level', 'unit_price',
            'is_active', 'stock_status', 'is_low_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'current_stock']


class InventoryTransactionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']


class PrescriptionDispenseSerializer(serializers.ModelSerializer):
    auto_calculated_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = PrescriptionDispense
        fields = [
            'id', 'prescription', 'medicine', 'quantity_dispensed',
            'auto_calculated_quantity', 'amount_charged',
            'pharmacist', 'notes', 'dispensed_at'
        ]
        read_only_fields = ['dispensed_at', 'pharmacist', 'auto_calculated_quantity']

    def _extract_number(self, text):
        match = re.search(r'\d+', str(text))
        return int(match.group()) if match else 1

    def _calculate_total_quantity(self, prescription):
        dosage_num = self._extract_number(prescription.dosage)
        duration_num = self._extract_number(prescription.duration)

        freq_match = re.search(r'(once|twice|thrice|\d+)', str(prescription.dosage).lower())
        if freq_match:
            freq_str = freq_match.group(1)
            if freq_str == 'once':
                freq = 1
            elif freq_str == 'twice':
                freq = 2
            elif freq_str == 'thrice':
                freq = 3
            else:
                freq = int(freq_str)
        else:
            freq = 1

        return dosage_num * freq * duration_num

    def validate(self, data):
        prescription = data.get('prescription')
        medicine = data.get('medicine')

        if prescription.status != 'PENDING':
            raise serializers.ValidationError(
                f"Cannot dispense a prescription with status '{prescription.status}'."
            )

        total_qty = self._calculate_total_quantity(prescription)
        data['auto_calculated_quantity'] = total_qty

        if not medicine.is_active:
            raise serializers.ValidationError("This medicine is inactive.")

        if medicine.current_stock < total_qty:
            raise serializers.ValidationError({
                "medicine": f"Insufficient stock. Available: {medicine.current_stock}, Needed: {total_qty}"
            })

        if not data.get('quantity_dispensed'):
            data['quantity_dispensed'] = total_qty

        return data


    def create(self, validated_data):
        request = self.context['request']
        validated_data['pharmacist'] = request.user

        with db_transaction.atomic():  # Ensure all operations are atomic
            dispense = super().create(validated_data)
            medicine = dispense.medicine
            qty = dispense.quantity_dispensed

            # Logging stock before dispensing
            logger.info(f"[DISPENSE START] Prescription #{dispense.prescription.id} | Medicine: {medicine.name} | Quantity: {qty} | Current stock: {medicine.current_stock}")

            # Create inventory transaction (automatically updates stock)
            inv_trans = InventoryTransaction.objects.create(
                medicine=medicine,
                transaction_type='DISPENSED',
                quantity=qty,
                prescription=dispense.prescription,
                notes=f"Dispensed for prescription #{dispense.prescription.id}",
                created_by=request.user
            )

            # Refresh stock after transaction and log
            medicine.refresh_from_db()
            logger.info(f"[DISPENSE END] Updated stock for {medicine.name}: {medicine.current_stock} | Transaction ID: {inv_trans.id}")

            # Update prescription status
            prescription = dispense.prescription
            prescription.status = 'DISPENSED'
            prescription.pharmacist = request.user
            prescription.save(update_fields=['status', 'pharmacist'])

        return dispense



class LowStockAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    current_stock = serializers.IntegerField()
    reorder_level = serializers.IntegerField()
    stock_status = serializers.CharField()
    stock_deficit = serializers.IntegerField()
