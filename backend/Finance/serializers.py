from rest_framework import serializers
from .models import Invoice, Payment, RevenueEntry, ExpenseEntry
from patients.serializers import PatientSerializer

class InvoiceSerializer(serializers.ModelSerializer):
	patient_detail = PatientSerializer(source='patient', read_only=True)
	class Meta:
		model = Invoice
		fields = ['id','patient','patient_detail','prescription','created_by','services','subtotal','discount','total','status','created_at','updated_at']
		read_only_fields = ['created_by','subtotal','total','created_at','updated_at']

	def create(self, validated_data):
		req = self.context.get('request')
		if req and req.user and req.user.is_authenticated:
			validated_data['created_by'] = req.user
		return super().create(validated_data)

class PaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment
		fields = ['id','invoice','recorded_by','amount','method','reference','created_at']
		read_only_fields = ['recorded_by','created_at']

	def validate(self, attrs):
		invoice = attrs.get('invoice') or getattr(self.instance, 'invoice', None)
		if invoice and invoice.status == 'VOID':
			raise serializers.ValidationError('Cannot pay a void invoice')
		return attrs

	def create(self, validated_data):
		req = self.context.get('request')
		if req and req.user and req.user.is_authenticated:
			validated_data['recorded_by'] = req.user
		obj = super().create(validated_data)
		inv = obj.invoice
		total_paid = sum(p.amount for p in inv.payments.all())
		if total_paid >= inv.total:
			inv.status = 'PAID'
			inv.save()
		try:
			RevenueEntry.objects.create(
				occurred_on=obj.created_at.date(),
				category=RevenueEntry.Category.INVOICE_PAYMENT,
				description=f"Invoice #{inv.id} payment via {obj.method}",
				amount=obj.amount,
				reference=obj.reference or '',
				invoice=inv,
				recorded_by=obj.recorded_by,
				metadata={'payment_id': obj.id}
			)
		except Exception:
			# Avoid breaking payment creation if revenue logging fails
			pass
		return obj


class RevenueEntrySerializer(serializers.ModelSerializer):
	recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

	class Meta:
		model = RevenueEntry
		fields = ['id','occurred_on','category','description','amount','reference','invoice','recorded_by','recorded_by_name','metadata','created_at','updated_at']
		read_only_fields = ['recorded_by','recorded_by_name','created_at','updated_at']

	def create(self, validated_data):
		req = self.context.get('request')
		if req and req.user and req.user.is_authenticated:
			validated_data.setdefault('recorded_by', req.user)
		return super().create(validated_data)


class ExpenseEntrySerializer(serializers.ModelSerializer):
	recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

	class Meta:
		model = ExpenseEntry
		fields = ['id','occurred_on','category','vendor','description','amount','reference','recorded_by','recorded_by_name','metadata','created_at','updated_at']
		read_only_fields = ['recorded_by','recorded_by_name','created_at','updated_at']

	def create(self, validated_data):
		req = self.context.get('request')
		if req and req.user and req.user.is_authenticated:
			validated_data.setdefault('recorded_by', req.user)
		return super().create(validated_data)
