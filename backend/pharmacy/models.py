from django.db import models, transaction as db_transaction
from django.db.models import F
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('SYRUP', 'Syrup'),
        ('INJECTION', 'Injection'),
        ('CREAM', 'Cream/Ointment'),
        ('DROPS', 'Drops'),
        ('INHALER', 'Inhaler'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    manufacturer = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Stock
    current_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_medicines')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level
    
    @property
    def stock_status(self):
        if self.current_stock == 0:
            return 'OUT_OF_STOCK'
        elif self.is_low_stock:
            return 'LOW_STOCK'
        return 'IN_STOCK'


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('STOCK_IN', 'Stock In'),
        ('STOCK_OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('DISPENSED', 'Dispensed'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    prescription = models.ForeignKey('emr.Prescription', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_transactions')
    notes = models.TextField(blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='inventory_transactions')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.medicine.name} ({self.quantity})"
    
    def clean(self):
        if self.transaction_type in ['STOCK_IN', 'STOCK_OUT', 'DISPENSED'] and self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1 for this transaction type.'})
        if self.pk is None and self.transaction_type in ['STOCK_OUT', 'DISPENSED']:
            if self.quantity > self.medicine.current_stock:
                raise ValidationError({'quantity': f'Insufficient stock. Available: {self.medicine.current_stock}'})
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        with db_transaction.atomic():
            if is_new:
                medicine = Medicine.objects.select_for_update().get(pk=self.medicine.pk)
            super().save(*args, **kwargs)
            if is_new:
                if self.transaction_type == 'STOCK_IN':
                    Medicine.objects.filter(pk=medicine.pk).update(current_stock=F('current_stock') + self.quantity)
                elif self.transaction_type in ['STOCK_OUT', 'DISPENSED']:
                    updated = Medicine.objects.filter(
                        pk=medicine.pk,
                        current_stock__gte=self.quantity
                    ).update(current_stock=F('current_stock') - self.quantity)
                    if not updated:
                        raise ValidationError(f'Insufficient stock for {medicine.name}.')
                elif self.transaction_type == 'ADJUSTMENT':
                    Medicine.objects.filter(pk=medicine.pk).update(current_stock=F('current_stock') + self.quantity)
                medicine.refresh_from_db()


class Prescription(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DISPENSED', 'Dispensed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    pharmacist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_prescriptions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} - {self.medication} ({self.status})"

    def mark_completed(self):
        if self.status != 'DISPENSED':
            raise ValidationError("Prescription must be dispensed before completion.")
        self.status = 'COMPLETED'
        self.save()

    def reinitiate(self):
        """Allows cancelled prescriptions to return to pending."""
        if self.status != 'CANCELLED':
            raise ValidationError("Only cancelled prescriptions can be reinitiated.")
        self.status = 'PENDING'
        self.save()


class PrescriptionDispense(models.Model):
    prescription = models.OneToOneField('emr.Prescription', on_delete=models.CASCADE, related_name='dispense_record')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity_dispensed = models.IntegerField(validators=[MinValueValidator(1)])
    pharmacist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='dispensed_medicines')
    amount_charged = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    notes = models.TextField(blank=True)
    dispensed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dispensed_at']
    
    def __str__(self):
        return f"Dispensed: {self.medicine.name} for {self.prescription.patient.username}"
