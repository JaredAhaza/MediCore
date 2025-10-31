from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class Command(BaseCommand):
	help = 'Test Finance APIs: Invoice and Payment'

	def add_arguments(self, parser):
		parser.add_argument('--no-reset', action='store_true')

	def handle(self, *args, **opts):
		if not opts.get('no_reset'):
			call_command('clean_test_data')
		self._ensure_users()
		client = self._login('test_finance')
		patient_id = self._ensure_patient()
		invoice_id, total = self._create_invoice(client, patient_id)
		self._record_payment(client, invoice_id, total)
		self.stdout.write(self.style.SUCCESS('✅ Finance tests passed'))

	def _ensure_users(self):
		for u, role in [('test_finance', User.Role.FINANCE), ('test_admin', User.Role.ADMIN)]:
			o, _ = User.objects.get_or_create(username=u, defaults={'email': f'{u}@ex.com','role': role})
			o.role = role; o.set_password('testpass123'); o.save()

	def _login(self, username):
		c = APIClient()
		r = c.post('/api/token/', {'username': username, 'password': 'testpass123'})
		if r.status_code != status.HTTP_200_OK: raise SystemExit('Login failed')
		c.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
		return c

	def _ensure_patient(self):
		from patients.models import Patient
		p, _ = Patient.objects.get_or_create(medical_id='FIN_TEST_1', defaults={'name':'Finance Test','gender':'OTHER'})
		return p.id

	def _create_invoice(self, client, patient_id):
		payload = {
			'patient': patient_id,
			'services': [{'code':'CONS','name':'Consultation','amount': 20.00},{'code':'LAB','name':'Lab','amount': 30.50}],
			'discount': 5.50
		}
		r = client.post('/api/invoices/', payload, format='json')
		if r.status_code != status.HTTP_201_CREATED: raise SystemExit(f'Create invoice failed: {r.status_code} {getattr(r,\"data\",\"\")}')
		return r.data['id'], r.data['total']

	def _record_payment(self, client, invoice_id, total):
		r = client.post('/api/payments/', {'invoice': invoice_id, 'amount': total, 'method':'CASH'}, format='json')
		if r.status_code != status.HTTP_201_CREATED: raise SystemExit('Record payment failed')
