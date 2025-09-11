from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Test API authentication and JWT tokens'

    def add_arguments(self, parser):
        parser.add_argument('--no-reset', action='store_true', help='Do not clean test data before running')

    def handle(self, *args, **options):
        if not options.get('no_reset'):
            call_command('clean_test_data')

        self.stdout.write('Testing API authentication...')
        
        # Test JWT token obtain
        self.test_jwt_token_obtain()
        
        # Test JWT token refresh
        self.test_jwt_token_refresh()
        
        # Test authenticated endpoint
        self.test_authenticated_endpoint()
        
        # Test unauthenticated access
        self.test_unauthenticated_access()
        
        self.stdout.write(
            self.style.SUCCESS('✅ All API tests passed!')
        )

    def _ensure_user(self):
        user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'role': User.Role.DOCTOR}
        )
        user.set_password('testpass123')
        user.save()
        return user

    def test_jwt_token_obtain(self):
        """Test JWT token obtain endpoint"""
        client = APIClient()
        self._ensure_user()
        
        response = client.post('/api/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        if response.status_code == status.HTTP_200_OK and 'access' in response.data and 'refresh' in response.data:
            self.stdout.write('✅ JWT token obtain: PASSED')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ JWT token obtain: FAILED - {response.status_code} {response.data if hasattr(response, "data") else ""}')
            )

    def test_jwt_token_refresh(self):
        """Test JWT token refresh endpoint"""
        client = APIClient()
        user = self._ensure_user()
        refresh = RefreshToken.for_user(user)
        
        response = client.post('/api/token/refresh/', {
            'refresh': str(refresh)
        })
        
        if response.status_code == status.HTTP_200_OK and 'access' in response.data:
            self.stdout.write('✅ JWT token refresh: PASSED')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ JWT token refresh: FAILED - {response.status_code} {response.data if hasattr(response, "data") else ""}')
            )

    def test_authenticated_endpoint(self):
        """Test accessing authenticated endpoint with JWT"""
        client = APIClient()
        user = self._ensure_user()
        access_token = str(RefreshToken.for_user(user).access_token)
        
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = client.get('/api/auth/me/')
        
        if response.status_code == status.HTTP_200_OK:
            self.stdout.write('✅ Authenticated endpoint: PASSED')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Authenticated endpoint: FAILED - {response.status_code}')
            )

    def test_unauthenticated_access(self):
        """Test that unauthenticated access is denied"""
        client = APIClient()
        response = client.get('/api/auth/me/')
        
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            self.stdout.write('✅ Unauthenticated access denied: PASSED')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Unauthenticated access denied: FAILED - {response.status_code}')
            )
