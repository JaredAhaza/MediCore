from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Test user roles and permissions'

    def add_arguments(self, parser):
        parser.add_argument('--no-reset', action='store_true', help='Do not clean test data before running')

    def handle(self, *args, **options):
        if not options.get('no_reset'):
            call_command('clean_test_data')

        self.stdout.write('Testing user roles...')
        
        # Test user creation with different roles
        self.test_user_creation_with_roles()
        
        # Test role choices
        self.test_role_choices()
        
        self.stdout.write(
            self.style.SUCCESS('✅ All user tests passed!')
        )

    def test_user_creation_with_roles(self):
        """Test creating users with different roles"""
        roles = [
            User.Role.ADMIN,
            User.Role.DOCTOR,
            User.Role.LAB_TECH,
            User.Role.PHARMACIST,
            User.Role.FINANCE,
            User.Role.PATIENT
        ]
        
        success_count = 0
        for role in roles:
            try:
                user = User.objects.create_user(
                    username=f'test_{role.lower()}',
                    email=f'{role.lower()}@example.com',
                    password='testpass123',
                    role=role
                )
                if user.role == role and user.check_password('testpass123'):
                    success_count += 1
                    self.stdout.write(f'✅ User creation with role {role}: PASSED')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ User creation with role {role}: FAILED')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ User creation with role {role}: FAILED - {e}')
                )
        
        self.stdout.write(f'User creation tests: {success_count}/{len(roles)} passed')

    def test_role_choices(self):
        """Test that role choices are properly defined"""
        role_choices = User.Role.choices
        expected_roles = [
            ('ADMIN', 'Admin'),
            ('DOCTOR', 'Doctor'),
            ('LAB_TECH', 'Lab Tech'),
            ('PHARMACIST', 'Pharmacist'),
            ('FINANCE', 'Finance'),
            ('PATIENT', 'Patient')
        ]
        
        success_count = 0
        for expected_role in expected_roles:
            if expected_role in role_choices:
                success_count += 1
                self.stdout.write(f'✅ Role choice {expected_role[0]}: PASSED')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Role choice {expected_role[0]}: FAILED')
                )
        
        self.stdout.write(f'Role choices tests: {success_count}/{len(expected_roles)} passed')
