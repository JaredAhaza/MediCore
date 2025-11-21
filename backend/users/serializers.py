from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ["id", "username", "email", "first_name", "last_name", "role", "password_change_required"]

class UserCreateSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
	password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
	
	class Meta:
		model = User
		fields = ["id", "username", "email", "first_name", "last_name", "role", "password", "password_confirm"]
		extra_kwargs = {
			'email': {'required': True},
			'first_name': {'required': True},
			'last_name': {'required': True},
		}
	
	def validate(self, attrs):
		if attrs.get('password') != attrs.get('password_confirm'):
			raise serializers.ValidationError({"password": "Password fields didn't match."})
		return attrs
	
	def create(self, validated_data):
		validated_data.pop('password_confirm')
		password = validated_data.pop('password')
		user = User.objects.create(**validated_data)
		user.set_password(password)
		# Mark password as temporary - user must change on first login
		user.password_change_required = True
		user.save()
		return user

class ChangePasswordSerializer(serializers.Serializer):
	old_password = serializers.CharField(required=True, write_only=True)
	new_password = serializers.CharField(required=True, write_only=True)
	new_password_confirm = serializers.CharField(required=True, write_only=True)
	
	def validate(self, attrs):
		if attrs.get('new_password') != attrs.get('new_password_confirm'):
			raise serializers.ValidationError({"new_password": "Password fields didn't match."})
		
		# Ensure new password is different from old password
		if attrs.get('old_password') == attrs.get('new_password'):
			raise serializers.ValidationError({"new_password": "New password must be different from the current password."})
		
		return attrs
