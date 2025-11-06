from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, Visit

User = get_user_model()

class PatientSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    username = serializers.CharField(write_only=False, required=True, source='user.username')

    class Meta:
        model = Patient
        fields = [
            "id", "username", "name", "dob", "gender", "gender_display",
            "contact", "medical_id", "created_at", "updated_at"
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
