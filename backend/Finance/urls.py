from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
	InvoiceViewSet,
	PaymentViewSet,
	RevenueEntryViewSet,
	ExpenseEntryViewSet,
	FinancialPositionReportView,
)

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'revenues', RevenueEntryViewSet, basename='revenue-entry')
router.register(r'expenses', ExpenseEntryViewSet, basename='expense-entry')

urlpatterns = [
	path('finance/reports/financial-position/', FinancialPositionReportView.as_view(), name='financial-position-report'),
	path('', include(router.urls)),
]
