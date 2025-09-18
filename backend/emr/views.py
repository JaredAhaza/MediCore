from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
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
    # Allow authenticated, enforce role logic per action below
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__name', 'patient__medical_id', 'medication']
    ordering_fields = ['created_at', 'status']

    def create(self, request, *args, **kwargs):
        role = getattr(request.user, 'role', None)
        if role not in {'ADMIN', 'DOCTOR'}:
            raise PermissionDenied('Only doctors or admins can create prescriptions')
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        role = getattr(request.user, 'role', None)
        if role in {'ADMIN', 'DOCTOR'}:
            return super().partial_update(request, *args, **kwargs)
        if role == 'PHARMACIST':
            # Pharmacists can only update status; set pharmacist user
            mutable_data = request.data.copy()
            allowed_fields = {'status'}
            filtered = {k: v for k, v in mutable_data.items() if k in allowed_fields}
            if not filtered:
                return Response({'detail': 'Only status can be updated by pharmacist'}, status=status.HTTP_400_BAD_REQUEST)
            # Inject pharmacist attribution
            filtered['pharmacist'] = request.user.id
            request._full_data = filtered  # for DRF serializer to read
            return super().partial_update(request, *args, **kwargs)
        raise PermissionDenied('You do not have permission to perform this action')

class TreatmentNoteViewSet(viewsets.ModelViewSet):
    queryset = TreatmentNote.objects.select_related('patient', 'doctor', 'visit').order_by('-created_at')
    serializer_class = TreatmentNoteSerializer
    permission_classes = [IsAuthenticated & IsDoctorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__name', 'patient__medical_id', 'diagnosis']
    ordering_fields = ['created_at']
