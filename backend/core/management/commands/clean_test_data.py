# backend/core/management/commands/clean_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
	help = 'Remove test data created by management test commands'

	def handle(self, *args, **options):
		qs = User.objects.filter(username__startswith='test_') | User.objects.filter(username='testuser')
		count = qs.count()
		qs.delete()
		self.stdout.write(self.style.SUCCESS(f'🧹 Removed {count} test users'))
