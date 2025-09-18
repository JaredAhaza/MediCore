from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from uuid import uuid4

User = get_user_model()


class Command(BaseCommand):
	help = 'Test EMR APIs: Prescriptions and Treatment Notes (CRUD + permissions)'

	def add_arguments(self, parser):
		parser.add_argument('--no-reset', action='store_true', help='Do not clean test data before running')

	def handle(self, *args, **options):
		if not options.get('no_reset'):
			call_command('clean_test_data')

		self.stdout.write('Testing EMR APIs (Prescriptions, Treatment Notes)...')
		self._seed_users()
		patient_id = self._ensure_patient()

		self._test_prescription_doctor_can_create(patient_id)
		self._test_prescription_pharmacist_can_update_status(patient_id)
		self._test_treatment_note_doctor_can_create(patient_id)
		self._test_non_doctor_cannot_write_emr(patient_id)

		self.stdout.write(self.style.SUCCESS('✅ EMR tests passed!'))

	def _seed_users(self):
		def mk(username, role):
			u, _ = User.objects.get_or_create(
				username=username,
				defaults={'email': f'{username}@example.com', 'role': role},
			)
			u.role = role
			u.set_password('testpass123')
			u.save()
			return u
		mk('test_doctor', getattr(User.Role, 'DOCTOR'))
		mk('test_pharmacist', getattr(User.Role, 'PHARMACIST'))
		mk('test_finance', getattr(User.Role, 'FINANCE'))

	def _login(self, username):
		client = APIClient()
		resp = client.post('/api/token/', {'username': username, 'password': 'testpass123'})
		if resp.status_code != status.HTTP_200_OK:
			raise RuntimeError(f'Login failed for {username}: {getattr(resp, "data", resp.status_code)}')
		client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
		return client

	def _ensure_patient(self):
		# Create a test patient via doctor
		doctor = self._login('test_doctor')
		payload = {
			'name': 'EMR Test Patient',
			'dob': '1990-01-01',
			'gender': 'OTHER',
			'contact': '555-9999',
			'medical_id': f'EMRTEST_{uuid4().hex[:8]}'.upper(),
		}
		r = doctor.post('/api/patients/', payload, format='json')
		if r.status_code != status.HTTP_201_CREATED:
			raise SystemExit(f'Failed to create patient for EMR tests: {r.status_code} {getattr(r, "data", "")}')
		return r.data['id']

	def _test_prescription_doctor_can_create(self, patient_id: int):
		client = self._login('test_doctor')
		payload = {
			'patient': patient_id,
			'medication': 'Amoxicillin',
			'dosage': '500mg',
			'duration': '7 days',
			'instructions': 'Take after meals',
			'status': 'PENDING',
		}
		r = client.post('/api/prescriptions/', payload, format='json')
		if r.status_code != status.HTTP_201_CREATED:
			self.stdout.write(self.style.ERROR(f'❌ Doctor create prescription failed - {r.status_code} {getattr(r, "data", {})}'))
			raise SystemExit(1)
		self.prescription_id = r.data['id']
		self.stdout.write('✅ Doctor can create prescription')

	def _test_prescription_pharmacist_can_update_status(self, patient_id: int):
		# Pharmacist should be able to update prescription status to DISPENSED
		client = self._login('test_pharmacist')
		prescription_id = getattr(self, 'prescription_id', None)
		if not prescription_id:
			raise SystemExit('Prescription not created in previous step')
		r = client.patch(f'/api/prescriptions/{prescription_id}/', {'status': 'DISPENSED'}, format='json')
		if r.status_code != status.HTTP_200_OK or r.data.get('status') != 'DISPENSED':
			self.stdout.write(self.style.ERROR(f'❌ Pharmacist update prescription failed - {r.status_code} {getattr(r, "data", {})}'))
			raise SystemExit(1)
		self.stdout.write('✅ Pharmacist can update prescription status')

	def _test_treatment_note_doctor_can_create(self, patient_id: int):
		client = self._login('test_doctor')
		payload = {
			'patient': patient_id,
			'diagnosis': 'Acute pharyngitis',
			'treatment_plan': 'Hydration and rest',
			'notes': 'TEST_NOTE',
		}
		r = client.post('/api/treatment-notes/', payload, format='json')
		if r.status_code != status.HTTP_201_CREATED:
			self.stdout.write(self.style.ERROR(f'❌ Doctor create treatment note failed - {r.status_code} {getattr(r, "data", {})}'))
			raise SystemExit(1)
		self.treatment_note_id = r.data['id']
		self.stdout.write('✅ Doctor can create treatment note')

	def _test_non_doctor_cannot_write_emr(self, patient_id: int):
		client = self._login('test_finance')
		# Try create prescription (should be forbidden)
		r1 = client.post('/api/prescriptions/', {
			'patient': patient_id,
			'medication': 'Ibuprofen',
			'dosage': '200mg',
			'duration': '3 days',
		}, format='json')
		if r1.status_code != status.HTTP_403_FORBIDDEN:
			self.stdout.write(self.style.ERROR(f'❌ Non-doctor create prescription should be forbidden (got {r1.status_code})'))
			raise SystemExit(1)
		# Try create treatment note (should be forbidden)
		r2 = client.post('/api/treatment-notes/', {
			'patient': patient_id,
			'diagnosis': 'X',
			'treatment_plan': 'Y',
		}, format='json')
		if r2.status_code != status.HTTP_403_FORBIDDEN:
			self.stdout.write(self.style.ERROR(f'❌ Non-doctor create treatment note should be forbidden (got {r2.status_code})'))
			raise SystemExit(1)
		self.stdout.write('✅ Non-doctor write access is denied as expected')


