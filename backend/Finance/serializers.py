from rest_framework import serializers
from .models import Invoice, Payment
from patients.serializers import PatientSerializer

class InvoiceSerializer(serializers.ModelSerializer):
	patient_detail = PatientSerializer(source='patient', read_only=True)
	class Meta:
		model = Invoice
		fields = ['id','patient','patient_detail','created_by','services','subtotal','discount','total','status','created_at','updated_at']
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
		return obj
