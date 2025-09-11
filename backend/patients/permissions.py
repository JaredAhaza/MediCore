from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsClinicianOrReadOnly(BasePermission):
	def has_permission(self, request, view):
		if request.method in SAFE_METHODS:
			return request.user and request.user.is_authenticated
		# Only Admin/Doctor/LabTech/Pharmacist can write patient/visit data
		role = getattr(request.user, "role", None)
		return role in {"ADMIN","DOCTOR","LAB_TECH","PHARMACIST"}
