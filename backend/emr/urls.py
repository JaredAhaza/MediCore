from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabReportViewSet, PrescriptionViewSet, TreatmentNoteViewSet

router = DefaultRouter()
router.register(r'lab-reports', LabReportViewSet, basename='labreport')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'treatment-notes', TreatmentNoteViewSet, basename='treatmentnote')

urlpatterns = [
    path('', include(router.urls)),
]