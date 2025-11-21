from django.shortcuts import render
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer
from .models import User
from .permissions import IsAdmin

# Create your views here.

class MeView(RetrieveAPIView):
	serializer_class = UserSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		return self.request.user

class UserViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for user management. Only accessible by admins.
	Supports listing, creating, and viewing users.
	"""
	queryset = User.objects.all().order_by('-date_joined')
	permission_classes = [IsAuthenticated, IsAdmin]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['username', 'email', 'first_name', 'last_name']
	ordering_fields = ['date_joined', 'username']
	filterset_fields = ['role', 'is_active']
	
	def get_serializer_class(self):
		if self.action == 'create':
			return UserCreateSerializer
		return UserSerializer
	
	# Restrict to list, retrieve, and create only (no update/delete for safety)
	http_method_names = ['get', 'post', 'head', 'options']

	@action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
	def change_password(self, request):
		"""
		Allow any authenticated user to change their own password.
		Validates that new password is different from old password.
		"""
		serializer = ChangePasswordSerializer(data=request.data)
		if serializer.is_valid():
			user = request.user
			
			# Check old password
			if not user.check_password(serializer.validated_data['old_password']):
				return Response(
					{"old_password": "Current password is incorrect."},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# Set new password
			user.set_password(serializer.validated_data['new_password'])
			# Clear the password change requirement
			user.password_change_required = False
			user.save()
			
			return Response(
				{"message": "Password changed successfully."},
				status=status.HTTP_200_OK
			)
		
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


