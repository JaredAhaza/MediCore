from rest_framework import serializers
from .models import LabReport, Prescription, TreatmentNote
from patients.serializers import PatientSerializer
from patients.models import Patient


class LabReportSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = LabReport
        fields = [
            'id', 'patient', 'patient_detail', 'lab_tech',
            'report_type', 'results', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['lab_tech']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['lab_tech'] = request.user
        return super().create(validated_data)


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient.patient_profile', read_only=True)
    patient_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_detail', 'patient_username',
            'doctor', 'pharmacist', 'medication', 'dosage', 'duration',
            'instructions', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['doctor', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Only validate patient on creation
        if self.instance is None:
            patient_username = attrs.get('patient_username')

            if patient_username:
                try:
                    patient_obj = Patient.objects.get(user__username=patient_username)
                    attrs['patient'] = patient_obj.user
                except Patient.DoesNotExist:
                    raise serializers.ValidationError({'patient_username': 'No patient with that username'})
            else:
                raise serializers.ValidationError({'patient_username': 'Patient username is required'})

            # Optional medication validation
            try:
                from pharmacy.models import Medicine
                med_name = attrs.get('medication')
                if med_name:
                    med = Medicine.objects.get(name=med_name, is_active=True)
                    if med.current_stock <= 0:
                        raise serializers.ValidationError({'medication': 'This medicine is out of stock.'})
            except ImportError:
                pass
            except Medicine.DoesNotExist:
                raise serializers.ValidationError({'medication': 'Selected medicine does not exist.'})

            attrs.pop('patient_username', None)
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['doctor'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Allow partial updates like status change"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class TreatmentNoteSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = TreatmentNote
        fields = [
            'id', 'patient', 'patient_detail', 'doctor', 'visit',
            'diagnosis', 'treatment_plan', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['doctor']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['doctor'] = request.user
        return super().create(validated_data)
