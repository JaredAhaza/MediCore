from django.db import models
from django.conf import settings

class LabReport(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='lab_reports')
    lab_tech = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='lab_reports')
    report_type = models.CharField(max_length=100)  # e.g., "Blood Test", "X-Ray", "MRI"
    results = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('REVIEWED', 'Reviewed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.report_type} - {self.patient.name} ({self.status})"

class Prescription(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='prescriptions')
    pharmacist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensed_prescriptions')
    medication = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)  # e.g., "7 days", "2 weeks"
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('DISPENSED', 'Dispensed'),
        ('COMPLETED', 'Completed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medication} - {self.patient.name} ({self.status})"

class TreatmentNote(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='treatment_notes')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='treatment_notes')
    visit = models.ForeignKey('patients.Visit', on_delete=models.CASCADE, null=True, blank=True, related_name='treatment_notes')
    diagnosis = models.CharField(max_length=200)
    treatment_plan = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Treatment - {self.patient.name} ({self.diagnosis})"