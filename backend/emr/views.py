from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import LabReport, Prescription, TreatmentNote
from .serializers import LabReportSerializer, PrescriptionSerializer, TreatmentNoteSerializer
from .permissions import IsLabTechOrReadOnly, IsDoctorOrReadOnly, IsPharmacistOrReadOnly

class LabReportViewSet(viewsets.ModelViewSet):
    queryset = LabReport.objects.select_related('patient', 'lab_tech').order_by('-created_at')
    serializer_class = LabReportSerializer
    permission_classes = [IsAuthenticated & IsLabTechOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__name', 'patient__medical_id', 'report_type']
    ordering_fields = ['created_at', 'status']

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.select_related('patient', 'doctor', 'pharmacist').order_by('-created_at')
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated & IsDoctorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__name', 'patient__medical_id', 'medication']
    ordering_fields = ['created_at', 'status']

class TreatmentNoteViewSet(viewsets.ModelViewSet):
    queryset = TreatmentNote.objects.select_related('patient', 'doctor', 'visit').order_by('-created_at')
    serializer_class = TreatmentNoteSerializer
    permission_classes = [IsAuthenticated & IsDoctorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__name', 'patient__medical_id', 'diagnosis']
    ordering_fields = ['created_at']
