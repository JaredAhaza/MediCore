from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
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

	@action(detail=True, methods=['post'])
	def void(self, request, pk=None):
		invoice = self.get_object()
		invoice.status = 'VOID'
		invoice.save()
		# If linked prescription is still pending, cancel it
		try:
			presc = invoice.prescription
			if presc and presc.status == 'PENDING':
				presc.status = 'CANCELLED'
				presc.save(update_fields=['status'])
		except Exception:
			pass
		return Response({'status': 'VOID'}, status=status.HTTP_200_OK)

	@action(detail=False, methods=['post'])
	def create_for_prescription(self, request):
		"""Create an invoice for a prescription, using medicine selling price.
		Expects: prescription (id), medicine (id), quantity (int, optional)
		"""
		try:
			from emr.models import Prescription as EMRPrescription
			from pharmacy.models import Medicine
			pid = int(request.data.get('prescription'))
			mid = int(request.data.get('medicine'))
			qty = int(request.data.get('quantity') or 1)
			presc = EMRPrescription.objects.get(pk=pid)
			med = Medicine.objects.get(pk=mid)
			amount = (med.selling_price or 0) * qty
			invoice = Invoice.objects.create(
				patient=presc.patient.patient_profile,
				prescription=presc,
				created_by=request.user,
				services=[{
					'code': f'MED-{med.id}',
					'name': f"{med.name} (x{qty})",
					'amount': float(amount)
				}]
			)
			ser = self.get_serializer(invoice)
			return Response(ser.data, status=status.HTTP_201_CREATED)
		except EMRPrescription.DoesNotExist:
			return Response({'detail': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)
		except Medicine.DoesNotExist:
			return Response({'detail': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentViewSet(viewsets.ModelViewSet):
	queryset = Payment.objects.select_related('invoice','recorded_by').order_by('-created_at')
	serializer_class = PaymentSerializer
	permission_classes = [IsAuthenticated & IsFinanceOrReadOnly]
	filter_backends = [filters.OrderingFilter]
	ordering_fields = ['created_at','amount']
