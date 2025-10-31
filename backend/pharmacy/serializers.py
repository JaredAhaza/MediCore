from rest_framework import serializers
from .models import Medicine, InventoryTransaction, PrescriptionDispense
from emr.models import Prescription


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
        fields = [
            'id', 'medicine', 'medicine_name', 'transaction_type', 'quantity',
            'prescription', 'notes', 'batch_number', 'expiry_date',
            'created_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'created_by']


class PrescriptionDispenseSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    patient_name = serializers.CharField(source='prescription.patient.name', read_only=True)
    pharmacist_name = serializers.CharField(source='pharmacist.username', read_only=True)
    prescription_details = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescriptionDispense
        fields = [
            'id', 'prescription', 'prescription_details', 'medicine', 'medicine_name',
            'quantity_dispensed', 'pharmacist', 'pharmacist_name', 'patient_name',
            'amount_charged', 'notes', 'dispensed_at'
        ]
        read_only_fields = ['dispensed_at', 'pharmacist']
    
    def get_prescription_details(self, obj):
        return {
            'id': obj.prescription.id,
            'medication': obj.prescription.medication,
            'dosage': obj.prescription.dosage,
            'duration': obj.prescription.duration,
            'patient': obj.prescription.patient.name
        }
    
    def create(self, validated_data):
        # Set pharmacist to current user
        validated_data['pharmacist'] = self.context['request'].user
        
        # Create dispense record
        dispense = super().create(validated_data)
        
        # Create inventory transaction
        InventoryTransaction.objects.create(
            medicine=dispense.medicine,
            transaction_type='DISPENSED',
            quantity=dispense.quantity_dispensed,
            prescription=dispense.prescription,
            notes=f"Dispensed for prescription #{dispense.prescription.id}",
            created_by=dispense.pharmacist
        )
        
        # Update prescription status
        prescription = dispense.prescription
        prescription.status = 'DISPENSED'
        prescription.pharmacist = dispense.pharmacist
        prescription.save()
        
        return dispense


class LowStockAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    current_stock = serializers.IntegerField()
    reorder_level = serializers.IntegerField()
    stock_status = serializers.CharField()
    stock_deficit = serializers.IntegerField()
