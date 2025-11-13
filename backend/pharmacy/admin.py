from django.contrib import admin
from .models import Medicine, InventoryTransaction, PrescriptionDispense


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_stock', 'reorder_level', 'stock_status', 'buying_price', 'selling_price', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'generic_name', 'manufacturer']
    readonly_fields = ['current_stock', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'category', 'manufacturer', 'description')
        }),
        ('Stock Management', {
            'fields': ('current_stock', 'reorder_level', 'buying_price', 'selling_price', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'transaction_type', 'quantity', 'batch_number', 'created_at', 'created_by']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['medicine__name', 'batch_number', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(PrescriptionDispense)
class PrescriptionDispenseAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'medicine', 'quantity_dispensed', 'pharmacist', 'amount_charged', 'dispensed_at']
    list_filter = ['dispensed_at', 'pharmacist']
    search_fields = ['prescription__patient__name', 'medicine__name']
    readonly_fields = ['dispensed_at']
    date_hierarchy = 'dispensed_at'
