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
    
    # Stock management
    current_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Metadata
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
    
    # Reference fields
    prescription = models.ForeignKey('emr.Prescription', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_transactions')
    
    # Details
    notes = models.TextField(blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='inventory_transactions')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.medicine.name} ({self.quantity})"
    
    def clean(self):
        super().clean()
        # Validate quantity based on transaction type
        if self.transaction_type in ['STOCK_IN', 'STOCK_OUT', 'DISPENSED'] and self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1 for this transaction type.'})
        
        # Validate sufficient stock for STOCK_OUT and DISPENSED
        if self.pk is None and self.transaction_type in ['STOCK_OUT', 'DISPENSED']:
            if self.quantity > self.medicine.current_stock:
                raise ValidationError({
                    'quantity': f'Insufficient stock. Available: {self.medicine.current_stock}'
                })
    
    def save(self, *args, **kwargs):
        # Update medicine stock based on transaction type
        is_new = self.pk is None
        
        # Use atomic transaction to ensure data integrity
        with db_transaction.atomic():
            # Lock the medicine row to prevent concurrent updates
            if is_new:
                medicine = Medicine.objects.select_for_update().get(pk=self.medicine.pk)
            
            super().save(*args, **kwargs)
            
            if is_new:
                # Use F() expressions for atomic database-level updates
                if self.transaction_type == 'STOCK_IN':
                    Medicine.objects.filter(pk=medicine.pk).update(
                        current_stock=F('current_stock') + self.quantity
                    )
                elif self.transaction_type in ['STOCK_OUT', 'DISPENSED']:
                    # Only update if sufficient stock exists
                    updated = Medicine.objects.filter(
                        pk=medicine.pk,
                        current_stock__gte=self.quantity
                    ).update(
                        current_stock=F('current_stock') - self.quantity
                    )
                    if not updated:
                        # Stock was insufficient - rollback will happen automatically
                        medicine.refresh_from_db()
                        raise ValidationError(
                            f'Insufficient stock for {medicine.name}. Available: {medicine.current_stock}, Requested: {self.quantity}'
                        )
                elif self.transaction_type == 'ADJUSTMENT':
                    # For adjustments, quantity can be negative
                    if self.quantity >= 0:
                        # Positive adjustment - just add
                        Medicine.objects.filter(pk=medicine.pk).update(
                            current_stock=F('current_stock') + self.quantity
                        )
                    else:
                        # Negative adjustment - ensure we don't go below 0
                        updated = Medicine.objects.filter(
                            pk=medicine.pk,
                            current_stock__gte=-self.quantity
                        ).update(
                            current_stock=F('current_stock') + self.quantity
                        )
                        if not updated:
                            # Would result in negative stock - clamp to 0
                            Medicine.objects.filter(pk=medicine.pk).update(current_stock=0)
                
                # Refresh the medicine instance to get updated values
                self.medicine.refresh_from_db()


class PrescriptionDispense(models.Model):
    prescription = models.OneToOneField('emr.Prescription', on_delete=models.CASCADE, related_name='dispense_record')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity_dispensed = models.IntegerField(validators=[MinValueValidator(1)])
    pharmacist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='dispensed_medicines')
    
    # Payment info (optional)
    amount_charged = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    notes = models.TextField(blank=True)
    dispensed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-dispensed_at']
    
    def __str__(self):
        return f"Dispensed: {self.medicine.name} for {self.prescription.patient.name}"
