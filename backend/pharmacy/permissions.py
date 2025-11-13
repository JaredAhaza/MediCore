from rest_framework import permissions


class IsPharmacyStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'PHARMACIST']


class CanDispensePrescription(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'PHARMACIST']


class CanImportInvoices(permissions.BasePermission):
    def has_permission(self, request, view):
        """Allow admins, pharmacists, and finance users to import/apply vendor invoices."""
        return request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'PHARMACIST', 'FINANCE']
