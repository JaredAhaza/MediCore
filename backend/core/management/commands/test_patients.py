# backend/core/management/commands/test_patients.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from uuid import uuid4

User = get_user_model()

CLINICIAN_ROLES = {"ADMIN","DOCTOR","LAB_TECH","PHARMACIST"}
NON_WRITE_ROLES = {"FINANCE","PATIENT"}


class Command(BaseCommand):
	help = 'Test Patients and Visits API (CRUD + permissions + search/order)'

	def add_arguments(self, parser):
		parser.add_argument('--no-reset', action='store_true', help='Do not clean test data before running')

	def handle(self, *args, **options):
		if not options.get('no_reset'):
			call_command('clean_test_data')

		self.stdout.write('Testing Patients & Visits APIs...')
		self._seed_users()

		self._test_clinician_crud_allowed()
		self._test_non_clinician_write_denied()
		self._test_search_and_ordering()

		self.stdout.write(self.style.SUCCESS('✅ Patients & Visits tests passed!'))

	def _seed_users(self):
		# One of each role
		def mk(role):
			u, created = User.objects.get_or_create(
				username=f"test_{role.lower()}",
				defaults={"email":f"{role.lower()}@example.com","role":getattr(User.Role, role)}
			)
			u.role = getattr(User.Role, role)
			u.set_password('testpass123')
			u.save()
			return u
		for role in list(CLINICIAN_ROLES | NON_WRITE_ROLES):
			mk(role)

	def _login(self, username):
		client = APIClient()
		resp = client.post('/api/token/', {'username': username, 'password': 'testpass123'})
		if resp.status_code != status.HTTP_200_OK:
			raise RuntimeError(f'Login failed for {username}: {getattr(resp,"data",resp.status_code)}')
		client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
		return client

	def _create_patient(self, client, idx=1, tag=""):
		payload = {
			"name": f"Test Patient {idx}",  # keep predictable for search
			"dob": "1990-01-01",
			"gender": "MALE",
			"contact": "555-0100",
			# ensure uniqueness via tag/uuid, not by changing the name
			"medical_id": f"TEST_{(tag or 'GEN')}_{idx:04d}_{uuid4().hex[:6]}".upper(),
		}
		return client.post('/api/patients/', payload, format='json')

	def _create_visit(self, client, patient_id, idx=1):
		payload = {
			"patient": patient_id,
			"date": timezone.now().isoformat(),
			"reason": f"TEST_Reason_{idx}",
			"notes": "Initial test visit"
		}
		return client.post('/api/visits/', payload, format='json')

	def _test_clinician_crud_allowed(self):
		for role in CLINICIAN_ROLES:
			client = self._login(f"test_{role.lower()}")

			# Create patient
			r = self._create_patient(client, idx=1, tag=role.lower())
			if r.status_code != status.HTTP_201_CREATED:
				self.stdout.write(self.style.ERROR(f'❌ {role}: create patient failed - {r.status_code} {getattr(r,"data","")}'))
				raise SystemExit(1)
			patient_id = r.data['id']

			# List patients
			r = client.get('/api/patients/')
			if r.status_code != status.HTTP_200_OK or not any(p['id']==patient_id for p in r.data):
				self.stdout.write(self.style.ERROR(f'❌ {role}: list patients failed'))
				raise SystemExit(1)

			# Update patient
			r = client.patch(f'/api/patients/{patient_id}/', {"contact":"555-0200"}, format='json')
			if r.status_code != status.HTTP_200_OK or r.data.get('contact') != '555-0200':
				self.stdout.write(self.style.ERROR(f'❌ {role}: update patient failed'))
				raise SystemExit(1)

			# Create visit (doctor auto-set in serializer)
			r = self._create_visit(client, patient_id, idx=1)
			if r.status_code != status.HTTP_201_CREATED:
				self.stdout.write(self.style.ERROR(f'❌ {role}: create visit failed - {r.status_code} {getattr(r,"data","")}'))
				raise SystemExit(1)

			self.stdout.write(f'✅ {role}: CRUD allowed')

	def _test_non_clinician_write_denied(self):
		for role in NON_WRITE_ROLES:
			client = self._login(f"test_{role.lower()}")

			# Try create patient → expect 403
			r = self._create_patient(client, idx=2, tag=role.lower())
			if r.status_code != status.HTTP_403_FORBIDDEN:
				self.stdout.write(self.style.ERROR(f'❌ {role}: create patient should be forbidden (got {r.status_code})'))
				raise SystemExit(1)

			# Read should be allowed
			r = client.get('/api/patients/')
			if r.status_code != status.HTTP_200_OK:
				self.stdout.write(self.style.ERROR(f'❌ {role}: read patients should be allowed'))
				raise SystemExit(1)

			self.stdout.write(f'✅ {role}: write denied, read allowed')

	def _test_search_and_ordering(self):
		# Use a clinician
		client = self._login("test_doctor")

		# Create a couple patients
		for i in range(3,5):
			self._create_patient(client, idx=i, tag="doctor")

		# Search by name
		r = client.get('/api/patients/?search=Test%20Patient%203')
		if r.status_code != status.HTTP_200_OK or not any('Test Patient 3' in p['name'] for p in r.data):
			self.stdout.write(self.style.ERROR('❌ Search by name failed'))
			raise SystemExit(1)

		# Ordering by name
		r = client.get('/api/patients/?ordering=name')
		if r.status_code != status.HTTP_200_OK:
			self.stdout.write(self.style.ERROR('❌ Ordering failed'))
			raise SystemExit(1)

		self.stdout.write('✅ Search and ordering OK')
