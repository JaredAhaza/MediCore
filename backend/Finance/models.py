from django.db import models
from django.conf import settings
from decimal import Decimal

# Create your models here.

class Invoice(models.Model):
	patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='invoices')
	prescription = models.ForeignKey('emr.Prescription', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
	services = models.JSONField(default=list)  # [{code, name, amount}]
	subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	status = models.CharField(max_length=20, choices=[('DUE','Due'),('PAID','Paid'),('VOID','Void')], default='DUE')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def recalc(self):
		# Ensure arithmetic uses Decimal consistently
		subtotal = Decimal('0')
		for s in (self.services or []):
			amt = s.get('amount', 0) or 0
			# Convert any float/int/string to Decimal safely
			try:
				subtotal += Decimal(str(amt))
			except Exception:
				# Skip invalid amounts rather than breaking invoice save
				continue
		self.subtotal = subtotal
		discount = self.discount if isinstance(self.discount, Decimal) else Decimal(str(self.discount or 0))
		total = self.subtotal - discount
		self.total = total if total > Decimal('0') else Decimal('0')

	def save(self, *args, **kwargs):
		self.recalc()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"Invoice #{self.id} for {self.patient}"

class Payment(models.Model):
	invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
	recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	method = models.CharField(max_length=30, choices=[('CASH','Cash'),('CARD','Card'),('MPESA','Mpesa'),('INSURANCE','Insurance')], default='CASH')
	reference = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Payment {self.amount} on Invoice #{self.invoice_id}"
