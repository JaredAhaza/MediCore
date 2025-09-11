# backend/core/management/commands/clean_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
	help = 'Remove test data created by management test commands'

	def handle(self, *args, **options):
		removed_users = User.objects.filter(
			Q(username__startswith='test_') | Q(username='testuser')
		).count()
		User.objects.filter(
			Q(username__startswith='test_') | Q(username='testuser')
		).delete()

		# Clean patients/visits created by tests
		try:
			from patients.models import Patient, Visit
			removed_visits = Visit.objects.filter(reason__startswith='TEST_').count()
			Visit.objects.filter(reason__startswith='TEST_').delete()

			removed_patients = Patient.objects.filter(medical_id__startswith='TEST_').count()
			Patient.objects.filter(medical_id__startswith='TEST_').delete()
		except Exception:
			removed_visits = 0
			removed_patients = 0

		self.stdout.write(self.style.SUCCESS(
			f'🧹 Removed {removed_users} test users, {removed_patients} test patients, {removed_visits} test visits'
		))
