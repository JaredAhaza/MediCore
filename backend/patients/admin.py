from django.contrib import admin
from .models import Patient, Visit

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
	list_display = ("id","name","medical_id","gender","dob","created_at")
	search_fields = ("name","medical_id","contact")

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
	list_display = ("id","patient","doctor","date","reason")
	list_filter = ("date",)
	search_fields = ("patient__name","patient__medical_id","reason")
