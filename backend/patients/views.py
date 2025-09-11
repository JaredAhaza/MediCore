from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Patient, Visit
from .serializers import PatientSerializer, VisitSerializer
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
