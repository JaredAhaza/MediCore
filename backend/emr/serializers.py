from rest_framework import serializers
from .models import LabReport, Prescription, TreatmentNote
from patients.serializers import PatientSerializer

class LabReportSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = LabReport
        fields = ['id', 'patient', 'patient_detail', 'lab_tech', 'report_type', 'results', 'status', 'created_at', 'updated_at']
        read_only_fields = ['lab_tech']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['lab_tech'] = request.user
        return super().create(validated_data)

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = Prescription
        fields = ['id', 'patient', 'patient_detail', 'doctor', 'pharmacist', 'medication', 'dosage', 'duration', 'instructions', 'status', 'created_at', 'updated_at']
        read_only_fields = ['doctor']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['doctor'] = request.user
        return super().create(validated_data)

class TreatmentNoteSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = TreatmentNote
        fields = ['id', 'patient', 'patient_detail', 'doctor', 'visit', 'diagnosis', 'treatment_plan', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['doctor']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['doctor'] = request.user
        return super().create(validated_data)