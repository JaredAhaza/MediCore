from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Patient, Visit, Prescription
from .serializers import PatientSerializer, VisitSerializer, PrescriptionSerializer
from .permissions import IsClinicianOrReadOnly

# Create your views here.

class PatientViewSet(viewsets.ModelViewSet):
	queryset = Patient.objects.all().order_by("-created_at")
	serializer_class = PatientSerializer
	permission_classes = [IsAuthenticated & IsClinicianOrReadOnly]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["name","medical_id","contact"]
	ordering_fields = ["created_at","name"]

class VisitViewSet(viewsets.ModelViewSet):
	queryset = Visit.objects.select_related("patient","doctor").order_by("-date")
	serializer_class = VisitSerializer
	permission_classes = [IsAuthenticated & IsClinicianOrReadOnly]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["patient__name","patient__medical_id","reason"]
	ordering_fields = ["date","created_at"]

class PrescriptionViewSet(viewsets.ModelViewSet):
	queryset = Prescription.objects.select_related("patient", "doctor", "pharmacist", "created_by").order_by("-created_at")
	serializer_class = PrescriptionSerializer
	permission_classes = [IsAuthenticated & IsClinicianOrReadOnly]
	parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["patient__name", "patient__medical_id", "medication"]
	ordering_fields = ["created_at", "status"]
	filterset_fields = ["status", "patient"]
