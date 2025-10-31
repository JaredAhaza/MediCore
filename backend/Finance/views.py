from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer
from .permissions import IsFinanceOrReadOnly

# Create your views here.

class InvoiceViewSet(viewsets.ModelViewSet):
	queryset = Invoice.objects.select_related('patient','created_by').order_by('-created_at')
	serializer_class = InvoiceSerializer
	permission_classes = [IsAuthenticated & IsFinanceOrReadOnly]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['patient__name','patient__medical_id']
	ordering_fields = ['created_at','total','status']

class PaymentViewSet(viewsets.ModelViewSet):
	queryset = Payment.objects.select_related('invoice','recorded_by').order_by('-created_at')
	serializer_class = PaymentSerializer
	permission_classes = [IsAuthenticated & IsFinanceOrReadOnly]
	filter_backends = [filters.OrderingFilter]
	ordering_fields = ['created_at','amount']
