from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Run all test commands'

    def handle(self, *args, **options):
        self.stdout.write('Running all tests...')
        self.stdout.write('=' * 50)

        self.stdout.write('\n0. Cleaning prior test data:')
        call_command('clean_test_data')

        self.stdout.write('\n1. Testing Database Connection:')
        call_command('test_db')

        self.stdout.write('\n2. Testing User Roles:')
        call_command('test_users', '--no-reset')

        self.stdout.write('\n3. Testing API Authentication:')
        call_command('test_api', '--no-reset')

        self.stdout.write('\n4. Testing Patients & Visits:')
        call_command('test_patients', '--no-reset')

        self.stdout.write('\n5. Testing EMR (Prescriptions & Treatment Notes):')
        call_command('test_emr', '--no-reset')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🎉 All tests completed!'))
