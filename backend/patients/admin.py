from django.contrib import admin
from .models import Patient, Visit, Prescription


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "medical_id", "gender", "dob", "created_at")
    search_fields = ("name", "medical_id", "contact", "user__username")


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "date", "reason")
    list_filter = ("date",)
    search_fields = ("patient__name", "patient__medical_id", "reason")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "medication", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("patient__name", "patient__user__username", "medication")
