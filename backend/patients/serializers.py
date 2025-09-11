from rest_framework import serializers
from .models import Patient, Visit

class PatientSerializer(serializers.ModelSerializer):
	class Meta:
		model = Patient
		fields = ["id","name","dob","gender","contact","medical_id","created_at","updated_at"]

class VisitSerializer(serializers.ModelSerializer):
	patient_detail = PatientSerializer(source="patient", read_only=True)

	class Meta:
		model = Visit
		fields = ["id","patient","patient_detail","doctor","date","reason","notes","created_at"]
		read_only_fields = ["doctor"]

	def create(self, validated_data):
		# default doctor to current user if provided
		request = self.context.get("request")
		if request and request.user and request.user.is_authenticated:
			validated_data.setdefault("doctor", request.user)
		return super().create(validated_data)
