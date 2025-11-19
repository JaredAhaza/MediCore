import re
import logging
from decimal import Decimal
from django.db import transaction as db_transaction
from rest_framework import serializers
from .models import Medicine, InventoryTransaction, PrescriptionDispense
from emr.models import Prescription
from Finance.models import Invoice


# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MedicineSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    # Reintroduce initial quantity for creation (write-only)
    quantity = serializers.IntegerField(write_only=True, required=False, min_value=0)

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'category', 'manufacturer',
            'description', 'current_stock', 'reorder_level', 'buying_price', 'selling_price',
            'quantity',
            'is_active', 'stock_status', 'is_low_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'current_stock']

    def create(self, validated_data):
        # Accept optional initial quantity on creation
        request = self.context.get('request')
        quantity = validated_data.pop('quantity', None)
        if quantity is not None:
            # Set initial current_stock from quantity
            validated_data['current_stock'] = quantity

        medicine = super().create(validated_data)

        # Create an initial stock transaction for audit trail
        try:
            if quantity and quantity > 0:
                InventoryTransaction.objects.create(
                    medicine=medicine,
                    transaction_type='STOCK_IN',
                    quantity=quantity,
                    notes='Initial stock on medicine creation',
                    created_by=(request.user if request else None)
                )
        except Exception:
            # Do not block medicine creation if transaction logging fails
            logger.exception("Failed to create initial STOCK_IN transaction for new medicine")

        return medicine


class InventoryTransactionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']


class PrescriptionDispenseSerializer(serializers.ModelSerializer):
    auto_calculated_quantity = serializers.SerializerMethodField(read_only=True)
    medicine_current_stock = serializers.SerializerMethodField(read_only=True)
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    final_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PrescriptionDispense
        fields = [
            'id', 'prescription', 'medicine', 'medicine_name', 'quantity_dispensed',
            'auto_calculated_quantity', 'amount_charged', 'discount_amount', 'additional_charges',
            'additional_charges_note', 'final_amount', 'pharmacist', 'notes', 'dispensed_at', 'medicine_current_stock'
        ]
        read_only_fields = ['dispensed_at', 'pharmacist', 'auto_calculated_quantity', 'medicine_current_stock', 'medicine_name', 'final_amount']

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

    def _normalize_decimal(self, value):
        try:
            return Decimal(str(value or '0')).quantize(Decimal('0.01'))
        except Exception:
            raise serializers.ValidationError('Invalid monetary amount supplied.')

    def validate(self, data):
        prescription = data.get('prescription')
        medicine = data.get('medicine')

        if prescription.status != 'PENDING':
            raise serializers.ValidationError(
                f"Cannot dispense a prescription with status '{prescription.status}'."
            )

        # Finance gating: require a PAID invoice linked to this prescription
        has_paid_invoice = Invoice.objects.filter(prescription=prescription, status='PAID').exists()
        if not has_paid_invoice:
            raise serializers.ValidationError({
                'prescription': 'Payment not approved. Dispensing requires a PAID invoice.'
            })

        # Category-based quantity logic
        requires_calc = medicine.category in {'TABLET', 'CAPSULE'}
        if requires_calc:
            total_qty = self._calculate_total_quantity(prescription)
        else:
            total_qty = None

        if not medicine.is_active:
            raise serializers.ValidationError("This medicine is inactive.")

        # Stock checks
        requested_qty = data.get('quantity_dispensed')
        if requires_calc:
            total_qty = total_qty or 1
            if medicine.current_stock < total_qty:
                raise serializers.ValidationError({
                    "medicine": f"Insufficient stock. Available: {medicine.current_stock}, Needed: {total_qty}"
                })
            if not requested_qty:
                data['quantity_dispensed'] = total_qty
        else:
            # For unit-sale categories, require quantity and validate against stock
            if not requested_qty or requested_qty < 1:
                raise serializers.ValidationError({'quantity_dispensed': 'Quantity is required for this medicine category.'})
            if medicine.current_stock < requested_qty:
                raise serializers.ValidationError({
                    "medicine": f"Insufficient stock. Available: {medicine.current_stock}, Needed: {requested_qty}"
                })

        discount = self._normalize_decimal(data.get('discount_amount', Decimal('0.00')))
        additional = self._normalize_decimal(data.get('additional_charges', Decimal('0.00')))
        base_amount = self._normalize_decimal(data.get('amount_charged', Decimal('0.00')))

        if discount < Decimal('0.00') or additional < Decimal('0.00'):
            raise serializers.ValidationError('Discount and additional charges must be zero or positive.')

        final_amount = base_amount - discount + additional
        if final_amount < Decimal('0.00'):
            raise serializers.ValidationError('Final amount cannot be negative.')

        data['amount_charged'] = base_amount
        data['discount_amount'] = discount
        data['additional_charges'] = additional
        note = (data.get('additional_charges_note') or '').strip()
        if additional > Decimal('0.00'):
            data['additional_charges_note'] = note or 'Additional Charges'
        else:
            data['additional_charges_note'] = ''

        return data


    def create(self, validated_data):
        request = self.context['request']
        validated_data['pharmacist'] = request.user
        # Remove any serializer-only fields that may have been set in validation
        validated_data.pop('auto_calculated_quantity', None)

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

    def get_auto_calculated_quantity(self, obj):
        try:
            med = obj.medicine
            presc = obj.prescription
            if med.category in {'TABLET', 'CAPSULE'}:
                return self._calculate_total_quantity(presc)
            return None
        except Exception:
            return None

    def get_medicine_current_stock(self, obj):
        try:
            return obj.medicine.current_stock
        except Exception:
            return None

    def get_final_amount(self, obj):
        try:
            return obj.final_amount
        except Exception:
            return None



class LowStockAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    current_stock = serializers.IntegerField()
    reorder_level = serializers.IntegerField()
    stock_status = serializers.CharField()
    stock_deficit = serializers.IntegerField()
