from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import LabReport, Prescription, TreatmentNote

@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'report_type', 'status', 'lab_tech', 'created_at')
    list_filter = ('status', 'report_type', 'created_at')
    search_fields = ('patient__name', 'patient__medical_id', 'report_type')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'medication', 'status', 'doctor', 'pharmacist', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('patient__name', 'patient__medical_id', 'medication')

@admin.register(TreatmentNote)
class TreatmentNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'diagnosis', 'doctor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient__name', 'patient__medical_id', 'diagnosis')