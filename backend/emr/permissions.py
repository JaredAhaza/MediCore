from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsLabTechOrReadOnly(BasePermission):
    """Only Lab Techs can create/update lab reports"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return getattr(request.user, 'role', None) in {'ADMIN', 'LAB_TECH'}

class IsDoctorOrReadOnly(BasePermission):
    """Only Doctors can create/update prescriptions and treatment notes"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return getattr(request.user, 'role', None) in {'ADMIN', 'DOCTOR'}

class IsPharmacistOrReadOnly(BasePermission):
    """Only Pharmacists can update prescription status"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return getattr(request.user, 'role', None) in {'ADMIN', 'PHARMACIST'}