from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
	"""
	Permission class that only allows users with ADMIN role.
	"""
	def has_permission(self, request, view):
		return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'
