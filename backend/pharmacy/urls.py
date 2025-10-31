from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicineViewSet, InventoryTransactionViewSet, PrescriptionDispenseViewSet

router = DefaultRouter()
router.register(r'medicines', MedicineViewSet, basename='medicine')
router.register(r'inventory-transactions', InventoryTransactionViewSet, basename='inventory-transaction')
router.register(r'dispense', PrescriptionDispenseViewSet, basename='prescription-dispense')

urlpatterns = [
    path('', include(router.urls)),
]
