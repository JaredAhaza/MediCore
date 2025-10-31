from django.contrib import admin
from .models import Invoice, Payment

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
	list_display = ('id','patient','total','status','created_at')
	search_fields = ('patient__name','patient__medical_id')
	list_filter = ('status','created_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('id','invoice','amount','method','created_at')
	list_filter = ('method','created_at')