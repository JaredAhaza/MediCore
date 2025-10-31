from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from .models import Medicine, InventoryTransaction, PrescriptionDispense
from .serializers import (
    MedicineSerializer, InventoryTransactionSerializer,
    PrescriptionDispenseSerializer, LowStockAlertSerializer
)
from .permissions import IsPharmacyStaff, CanDispensePrescription


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsPharmacyStaff]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'generic_name', 'manufacturer']
    ordering_fields = ['name', 'current_stock', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock_medicines = Medicine.objects.filter(
            current_stock__lte=F('reorder_level'),
            is_active=True
        ).order_by('current_stock')
        
        alerts = []
        for medicine in low_stock_medicines:
            alerts.append({
                'id': medicine.id,
                'name': medicine.name,
                'category': medicine.category,
                'current_stock': medicine.current_stock,
                'reorder_level': medicine.reorder_level,
                'stock_status': medicine.stock_status,
                'stock_deficit': medicine.reorder_level - medicine.current_stock
            })
        
        serializer = LowStockAlertSerializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        out_of_stock = Medicine.objects.filter(current_stock=0, is_active=True)
        serializer = self.get_serializer(out_of_stock, many=True)
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
    
    @action(detail=False, methods=['post'])
    def stock_in(self, request):
        data = request.data.copy()
        data['transaction_type'] = 'STOCK_IN'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def stock_out(self, request):
        data = request.data.copy()
        data['transaction_type'] = 'STOCK_OUT'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        medicine = Medicine.objects.get(id=data['medicine'])
        if medicine.current_stock < int(data['quantity']):
            return Response(
                {'error': 'Insufficient stock available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PrescriptionDispenseViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionDispense.objects.all()
    serializer_class = PrescriptionDispenseSerializer
    permission_classes = [CanDispensePrescription]
    filterset_fields = ['medicine', 'pharmacist', 'prescription']
    ordering_fields = ['dispensed_at']
    
    def create(self, request, *args, **kwargs):
        # Check if prescription already dispensed
        prescription_id = request.data.get('prescription')
        if PrescriptionDispense.objects.filter(prescription_id=prescription_id).exists():
            return Response(
                {'error': 'This prescription has already been dispensed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check stock availability
        medicine_id = request.data.get('medicine')
        quantity = int(request.data.get('quantity_dispensed', 0))
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            if medicine.current_stock < quantity:
                return Response(
                    {'error': f'Insufficient stock. Available: {medicine.current_stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Medicine.DoesNotExist:
            return Response(
                {'error': 'Medicine not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return super().create(request, *args, **kwargs)
