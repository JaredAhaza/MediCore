from django.contrib import admin
from .models import Invoice, Payment, RevenueEntry, ExpenseEntry

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
	list_display = ('id','patient','total','status','created_at')
	search_fields = ('patient__name','patient__medical_id')
	list_filter = ('status','created_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('id','invoice','amount','method','created_at')
	list_filter = ('method','created_at')


@admin.register(RevenueEntry)
class RevenueEntryAdmin(admin.ModelAdmin):
	list_display = ('id','occurred_on','category','amount','invoice','recorded_by')
	search_fields = ('description','reference')
	list_filter = ('category','occurred_on')


@admin.register(ExpenseEntry)
class ExpenseEntryAdmin(admin.ModelAdmin):
	list_display = ('id','occurred_on','category','vendor','amount','recorded_by')
	search_fields = ('vendor','description','reference')
	list_filter = ('category','occurred_on')