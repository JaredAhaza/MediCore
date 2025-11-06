from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, Q
from django.db import transaction
from .models import Medicine, InventoryTransaction, PrescriptionDispense
from .serializers import (
    MedicineSerializer,
    InventoryTransactionSerializer,
    PrescriptionDispenseSerializer,
    LowStockAlertSerializer
)
from .permissions import IsPharmacyStaff, CanDispensePrescription


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsPharmacyStaff]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'generic_name', 'manufacturer']
    ordering_fields = ['name', 'current_stock', 'created_at']

    def get_queryset(self):
        qs = Medicine.objects.all()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        ordering = self.request.query_params.get('ordering')
        if ordering:
            qs = qs.order_by(ordering)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        meds = Medicine.objects.filter(current_stock__lte=F('reorder_level'), is_active=True)
        alerts = [{
            'id': m.id,
            'name': m.name,
            'category': m.category,
            'current_stock': m.current_stock,
            'reorder_level': m.reorder_level,
            'stock_status': m.stock_status,
            'stock_deficit': m.reorder_level - m.current_stock
        } for m in meds]
        serializer = LowStockAlertSerializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        meds = Medicine.objects.filter(current_stock=0, is_active=True)
        serializer = self.get_serializer(meds, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transaction_history(self, request, pk=None):
        medicine = self.get_object()
        transactions = medicine.transactions.all()
        serializer = InventoryTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class InventoryTransactionViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsPharmacyStaff]
    filterset_fields = ['medicine', 'transaction_type', 'created_by']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PrescriptionDispenseViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionDispense.objects.all()
    serializer_class = PrescriptionDispenseSerializer
    permission_classes = [CanDispensePrescription]
    filterset_fields = ['medicine', 'pharmacist', 'prescription']
    ordering_fields = ['dispensed_at']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
