from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, Visit, Prescription

User = get_user_model()

class PatientSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    username = serializers.CharField(write_only=False, required=True, source='user.username')

    class Meta:
        model = Patient
        fields = [
            "id", "username", "name", "dob", "gender", "gender_display",
            "contact", "medical_id", "created_at", "updated_at", "address"
        ]
        read_only_fields = ["medical_id"]

    def create(self, validated_data):
        user_data = validated_data.pop("user", {})
        username = user_data.get("username")

        # Try to get or create the user
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password("default123")
            user.save()

        validated_data["user"] = user

        # Auto-generate medical ID
        last_patient = Patient.objects.order_by('-id').first()
        next_num = (last_patient.id if last_patient else 0) + 1
        validated_data["medical_id"] = f"PAT-{next_num:04d}"

        return super().create(validated_data)




class VisitSerializer(serializers.ModelSerializer):
	patient_detail = PatientSerializer(source="patient", read_only=True)

	class Meta:
		model = Visit
		fields = ["id", "patient", "patient_detail", "doctor", "date", "reason", "notes", "created_at"]
		read_only_fields = ["doctor"]

	def create(self, validated_data):
		# Default doctor to current user if provided
		request = self.context.get("request")
		if request and request.user and request.user.is_authenticated:
			validated_data.setdefault("doctor", request.user)
		return super().create(validated_data)


class PrescriptionSerializer(serializers.ModelSerializer):
	patient_detail = PatientSerializer(source="patient", read_only=True)
	patient_username = serializers.CharField(write_only=True, required=False)
	doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
	created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
	prescription_image_url = serializers.SerializerMethodField()

	class Meta:
		model = Prescription
		fields = [
			"id", "patient", "patient_detail", "patient_username", "doctor", "doctor_name",
			"medication", "dosage", "duration", "instructions", "status",
			"pharmacist", "prescription_image", "prescription_image_url",
			"created_by", "created_by_name", "created_at", "updated_at"
		]
		read_only_fields = ["created_by", "created_at", "updated_at", "patient"]

	def get_prescription_image_url(self, obj):
		if obj.prescription_image:
			request = self.context.get('request')
			if request:
				return request.build_absolute_uri(obj.prescription_image.url)
			return obj.prescription_image.url
		return None

	def create(self, validated_data):
		# Handle patient_username if provided
		patient_username = validated_data.pop('patient_username', None)
		if patient_username:
			try:
				from .models import Patient
				patient = Patient.objects.get(user__username=patient_username)
				validated_data['patient'] = patient
			except Patient.DoesNotExist:
				raise serializers.ValidationError({"patient_username": "Patient not found with this username"})
		
		# Set created_by to current user
		request = self.context.get("request")
		if request and request.user and request.user.is_authenticated:
			validated_data["created_by"] = request.user
			# If no doctor specified and user is a doctor, set as doctor
			if not validated_data.get("doctor") and request.user.role == "DOCTOR":
				validated_data["doctor"] = request.user
		return super().create(validated_data)
