from django.db import models
from django.conf import settings

# Create your models here.

class Patient(models.Model):
	name = models.CharField(max_length=255)
	dob = models.DateField(null=True, blank=True)
	gender = models.CharField(max_length=20, choices=[("MALE","Male"),("FEMALE","Female"),("OTHER","Other")], blank=True)
	contact = models.CharField(max_length=255, blank=True)
	medical_id = models.CharField(max_length=100, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} ({self.medical_id})"

class Visit(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="visits")
	doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="doctor_visits")
	date = models.DateTimeField()
	reason = models.CharField(max_length=255, blank=True)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Visit {self.id} - {self.patient} on {self.date:%Y-%m-%d}"
