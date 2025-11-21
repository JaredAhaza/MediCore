from datetime import date
from decimal import Decimal
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Sum
from django.db.models.functions import Coalesce
import csv
import io
from .models import Invoice, Payment, RevenueEntry, ExpenseEntry
from .serializers import InvoiceSerializer, PaymentSerializer, RevenueEntrySerializer, ExpenseEntrySerializer
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
		Expects: prescription (id), medicine (id), quantity (int, optional), discount?, additional_charges?
		"""
		try:
			from patients.models import Prescription
			from pharmacy.models import Medicine
			pid = int(request.data.get('prescription'))
			mid = int(request.data.get('medicine'))
			qty = int(request.data.get('quantity') or 1)
			discount_raw = request.data.get('discount') or request.data.get('discount_amount') or 0
			additional_raw = request.data.get('additional_charges') or 0
			additional_label = (request.data.get('additional_label') or request.data.get('additional_charges_note') or 'Additional Charges').strip() or 'Additional Charges'
			try:
				discount = Decimal(str(discount_raw))
				additional_charges = Decimal(str(additional_raw))
			except Exception:
				return Response({'detail': 'Invalid monetary values for discount or additional charges'}, status=status.HTTP_400_BAD_REQUEST)
			if discount < 0 or additional_charges < 0:
				return Response({'detail': 'Discount and additional charges must be zero or positive'}, status=status.HTTP_400_BAD_REQUEST)
			presc = Prescription.objects.get(pk=pid)
			med = Medicine.objects.get(pk=mid)
			amount = Decimal(str(med.selling_price or 0)) * qty
			services = [{
				'code': f'MED-{med.id}',
				'name': f"{med.name} (x{qty})",
				'amount': float(amount)
			}]
			if additional_charges > 0:
				services.append({
					'code': 'ADD-CHARGE',
					'name': additional_label,
					'amount': float(additional_charges)
				})
			invoice = Invoice.objects.create(
				patient=presc.patient,
				prescription=presc,
				created_by=request.user,
				discount=discount,
				services=services
			)
			ser = self.get_serializer(invoice)
			return Response(ser.data, status=status.HTTP_201_CREATED)
		except Prescription.DoesNotExist:
			return Response({'detail': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)
		except Medicine.DoesNotExist:
			return Response({'detail': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

	@action(detail=True, methods=['get'], url_path='download')
	def download(self, request, pk=None):
		"""Download a single invoice as CSV"""
		invoice = self.get_object()
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.csv"'
		
		writer = csv.writer(response)
		writer.writerow(['Invoice ID', invoice.id])
		writer.writerow(['Patient', invoice.patient.name])
		writer.writerow(['Medical ID', invoice.patient.medical_id])
		writer.writerow(['Status', invoice.status])
		writer.writerow(['Created At', invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')])
		writer.writerow(['Created By', invoice.created_by.username if invoice.created_by else 'N/A'])
		writer.writerow([])
		writer.writerow(['Services/Items'])
		writer.writerow(['Code', 'Name', 'Amount'])
		
		for service in (invoice.services or []):
			writer.writerow([
				service.get('code', ''),
				service.get('name', ''),
				f"Kshs {service.get('amount', 0):.2f}"
			])
		
		writer.writerow([])
		writer.writerow(['Subtotal', f"Kshs {invoice.subtotal:.2f}"])
		writer.writerow(['Discount', f"Kshs {invoice.discount:.2f}"])
		writer.writerow(['Total', f"Kshs {invoice.total:.2f}"])
		
		if invoice.prescription:
			writer.writerow([])
			writer.writerow(['Prescription ID', invoice.prescription.id])
			writer.writerow(['Medication', invoice.prescription.medication])
		
		return response

	@action(detail=False, methods=['get'], url_path='download-all')
	def download_all(self, request):
		"""Download all invoices (with optional filtering) as CSV"""
		queryset = self.filter_queryset(self.get_queryset())
		
		# Apply date filtering if provided
		start_date = request.query_params.get('start_date')
		end_date = request.query_params.get('end_date')
		status_filter = request.query_params.get('status')
		
		if start_date:
			start = parse_date(start_date)
			if start:
				queryset = queryset.filter(created_at__date__gte=start)
		if end_date:
			end = parse_date(end_date)
			if end:
				queryset = queryset.filter(created_at__date__lte=end)
		if status_filter:
			queryset = queryset.filter(status=status_filter)
		
		response = HttpResponse(content_type='text/csv')
		filename = f"invoices_{date.today().isoformat()}.csv"
		response['Content-Disposition'] = f'attachment; filename="{filename}"'
		
		writer = csv.writer(response)
		writer.writerow([
			'Invoice ID', 'Patient Name', 'Medical ID', 'Status', 'Subtotal', 
			'Discount', 'Total', 'Created At', 'Created By', 'Prescription ID'
		])
		
		for invoice in queryset:
			services_summary = ', '.join([s.get('name', '') for s in (invoice.services or [])[:3]])
			if len(invoice.services or []) > 3:
				services_summary += '...'
			
			writer.writerow([
				invoice.id,
				invoice.patient.name,
				invoice.patient.medical_id,
				invoice.status,
				f"{invoice.subtotal:.2f}",
				f"{invoice.discount:.2f}",
				f"{invoice.total:.2f}",
				invoice.created_at.strftime('%Y-%m-%d %H:%M:%S'),
				invoice.created_by.username if invoice.created_by else 'N/A',
				invoice.prescription.id if invoice.prescription else 'N/A'
			])
		
		return response

class PaymentViewSet(viewsets.ModelViewSet):
	queryset = Payment.objects.select_related('invoice','recorded_by').order_by('-created_at')
	serializer_class = PaymentSerializer
	permission_classes = [IsAuthenticated & IsFinanceOrReadOnly]
	filter_backends = [filters.OrderingFilter]
	ordering_fields = ['created_at','amount']


class BaseFinanceEntryViewSet(viewsets.ModelViewSet):
	"""
	Shared filtering logic for revenue and expense entries.
	"""
	date_field = 'occurred_on'
	permission_classes = [IsAuthenticated & IsFinanceOrReadOnly]

	def get_queryset(self):
		qs = super().get_queryset()
		start = self.request.query_params.get('start_date')
		end = self.request.query_params.get('end_date')
		if start:
			start_date = parse_date(start)
			if start_date:
				qs = qs.filter(**{f'{self.date_field}__gte': start_date})
		if end:
			end_date = parse_date(end)
			if end_date:
				qs = qs.filter(**{f'{self.date_field}__lte': end_date})
		category = self.request.query_params.get('category')
		if category:
			qs = qs.filter(category=category)
		return qs


class RevenueEntryViewSet(BaseFinanceEntryViewSet):
	queryset = RevenueEntry.objects.select_related('invoice','recorded_by').order_by('-occurred_on','-created_at')
	serializer_class = RevenueEntrySerializer


class ExpenseEntryViewSet(BaseFinanceEntryViewSet):
	queryset = ExpenseEntry.objects.select_related('recorded_by').order_by('-occurred_on','-created_at')
	serializer_class = ExpenseEntrySerializer


class FinancialPositionReportView(APIView):
	permission_classes = [IsAuthenticated & IsFinanceOrReadOnly]

	def _resolve_dates(self, request):
		today = date.today()
		start_param = request.query_params.get('start_date')
		end_param = request.query_params.get('end_date')
		if start_param:
			start = parse_date(start_param) or today.replace(day=1)
		else:
			start = today.replace(day=1)
		if end_param:
			end = parse_date(end_param) or today
		else:
			end = today
		if end < start:
			start, end = end, start
		return start, end

	def get(self, request):
		start, end = self._resolve_dates(request)

		revenue_qs = RevenueEntry.objects.filter(occurred_on__range=(start, end))
		expense_qs = ExpenseEntry.objects.filter(occurred_on__range=(start, end))
		payment_qs = Payment.objects.filter(created_at__date__range=(start, end))

		revenue_total = revenue_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total'] or Decimal('0')
		expense_total = expense_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total'] or Decimal('0')
		net_position = revenue_total - expense_total

		revenue_breakdown = list(
			revenue_qs.values('category').annotate(total=Coalesce(Sum('amount'), Decimal('0'))).order_by('-total')
		)
		expense_breakdown = list(
			expense_qs.values('category').annotate(total=Coalesce(Sum('amount'), Decimal('0'))).order_by('-total')
		)

		accounts_receivable = Invoice.objects.filter(status='DUE').aggregate(
			total=Coalesce(Sum('total'), Decimal('0'))
		)['total'] or Decimal('0')
		cash_collected = payment_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total'] or Decimal('0')

		return Response({
			'period': {'start_date': start.isoformat(), 'end_date': end.isoformat()},
			'totals': {
				'revenue': revenue_total,
				'expenses': expense_total,
				'net_position': net_position,
				'accounts_receivable': accounts_receivable,
				'cash_collected': cash_collected,
			},
			'breakdown': {
				'revenue_by_category': revenue_breakdown,
				'expenses_by_category': expense_breakdown,
			}
		})
