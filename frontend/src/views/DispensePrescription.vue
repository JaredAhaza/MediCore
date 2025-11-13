<template>
  <div>
    <div class="card">
      <h3>Dispense Prescription</h3>
      <p>Dispense medicine to patients with active prescriptions</p>
    </div>

    <div class="card">
      <h4>Select Prescription</h4>
      <div style="margin-bottom: 20px;">
        <input v-model="searchQuery" placeholder="Search by patient name or prescription ID..." @input="debouncedLoad" />
      </div>

      <div v-if="prescriptions.length === 0" style="text-align: center; color: #999; padding: 20px;">
        No pending prescriptions found
      </div>

      <div v-for="prescription in prescriptions" :key="prescription.id" class="prescription-card">
        <div style="display: flex; justify-content: space-between; align-items: start;">
          <div>
            <strong>{{ prescription.patient.name }}</strong>
            <div style="font-size: 0.9em; color: #666; margin: 5px 0;">
              Medication: <strong>{{ prescription.medication }}</strong>
            </div>
            <div style="font-size: 0.85em; color: #999;">
              Dosage: {{ prescription.dosage }} | Duration: {{ prescription.duration }}
            </div>
            <div v-if="prescription.instructions" style="font-size: 0.85em; color: #666; margin-top: 5px;">
              Instructions: {{ prescription.instructions }}
            </div>
          </div>
          <div>
            <span :style="getStatusBadge(prescription.status)">{{ prescription.status }}</span>
            <button v-if="prescription.status === 'PENDING'" @click="selectPrescription(prescription)" class="btn" style="margin-top: 10px;">
              Dispense
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedPrescription" class="card" style="border: 2px solid #0984e3;">
      <h4>Dispense Form</h4>
      <form @submit.prevent="dispense">
        <div style="display: grid; gap: 15px;">
          <div class="info-box">
            <strong>Patient:</strong> {{ selectedPrescription.patient.name }}<br />
            <strong>Medication:</strong> {{ selectedPrescription.medication }}<br />
            <strong>Dosage:</strong> {{ selectedPrescription.dosage }} | <strong>Duration:</strong> {{ selectedPrescription.duration }}
          </div>

          <div>
            <label>Select Medicine from Inventory *</label>
            <select v-model="dispenseForm.medicine" required @change="onMedicineSelect">
              <option value="">Select Medicine</option>
              <option v-for="med in availableMedicines" :key="med.id" :value="med.id">
                {{ med.name }} (Stock: {{ med.current_stock }})
              </option>
            </select>
          </div>

          <div v-if="selectedMedicine" class="info-box" style="background: #fff3cd;">
            <strong>{{ selectedMedicine.name }}</strong><br />
            Available Stock: <strong>{{ selectedMedicine.current_stock }}</strong> | 
            Selling Price: Kshs {{ selectedMedicine.selling_price }}
          </div>

          <div>
            <label>Quantity to Dispense *</label>
            <input v-model.number="dispenseForm.quantity_dispensed" type="number" min="1" required />
          </div>

          <div>
            <label>Amount to Charge (Kshs) *</label>
            <input v-model.number="dispenseForm.amount_charged" type="number" step="0.01" min="0" required />
            <small v-if="selectedMedicine" style="color: #666;">
              Suggested: Kshs {{ (selectedMedicine.selling_price * dispenseForm.quantity_dispensed).toFixed(2) }}
            </small>
          </div>

          <div>
            <label>Notes</label>
            <textarea v-model="dispenseForm.notes" rows="3" placeholder="Optional notes"></textarea>
          </div>

          <div style="display: flex; gap: 10px; align-items: center;">
            <button type="submit" class="btn" :disabled="isLoading || !currentInvoice || currentInvoice.status !== 'PAID'">{{ isLoading ? 'Processing...' : 'Complete Dispensing' }}</button>
            <button type="button" @click="cancelDispense" class="btn btn-secondary" :disabled="isLoading">Cancel</button>
            <button type="button" class="btn" style="background:#00b894;" @click="generateInvoice" :disabled="isLoading || !selectedMedicine">Generate Invoice</button>
            <button type="button" class="btn" style="background:#6c5ce7;" @click="recordPayment" :disabled="isLoading || !currentInvoice">Record Payment</button>
            <span v-if="isLoading" style="color: #666;">Updating inventory…</span>
          </div>

          <div v-if="currentInvoice" class="info-box" style="background:#f1f2f6;">
            <div>
              <strong>Invoice #{{ currentInvoice.id }}</strong> • Status: 
              <span :style="getStatusBadge(currentInvoice.status)">{{ currentInvoice.status }}</span>
            </div>
            <div style="font-size:0.9em; color:#555;">
              Subtotal: Kshs {{ currentInvoice.subtotal }} • Discount: Kshs {{ currentInvoice.discount }} • Total: Kshs {{ currentInvoice.total }}
            </div>
          </div>

          <div v-if="error" style="color: #d63031; padding: 10px; background: #fee; border-radius: 4px;">
            {{ error }}
          </div>
        </div>
      </form>
    </div>

    <div class="card">
      <h4>Recent Dispensed Prescriptions</h4>
      <div v-for="disp in recentDispenses" :key="disp.id" style="padding: 10px; border-bottom: 1px solid #eee;">
        <div style="display: flex; justify-content: space-between;">
          <div>
            <strong>{{ disp.patient_name }}</strong> • {{ disp.medicine_name }}
          </div>
          <div>
            Qty: {{ disp.quantity_dispensed }} • Kshs {{ disp.amount_charged }}
          </div>
        </div>
        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
          {{ new Date(disp.dispensed_at).toLocaleString() }} • By: {{ disp.pharmacist_name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/client';

const prescriptions = ref([]);
const router = useRouter();
const availableMedicines = ref([]);
const recentDispenses = ref([]);
const selectedPrescription = ref(null);
const currentInvoice = ref(null);
const selectedMedicine = ref(null);
const searchQuery = ref('');
const error = ref('');
const isLoading = ref(false);
let timer;

const dispenseForm = ref({
  prescription: '',
  medicine: '',
  quantity_dispensed: 1,
  amount_charged: 0,
  notes: ''
});

async function loadPrescriptions() {
  try {
    const params = { status: 'PENDING' };
    if (searchQuery.value) params.search = searchQuery.value;

    const { data } = await api.get('/api/prescriptions/', { params });
    prescriptions.value = data;
  } catch (err) {
    console.error('Failed to load prescriptions:', err);
  }
}

async function loadMedicines() {
  try {
    const { data } = await api.get('/api/pharmacy/medicines/', { params: { is_active: true } });
    availableMedicines.value = data.filter(m => m.current_stock > 0);
  } catch (err) {
    console.error('Failed to load medicines:', err);
  }
}

async function loadRecentDispenses() {
  try {
    const { data } = await api.get('/api/pharmacy/dispense/');
    recentDispenses.value = data.slice(0, 10);
  } catch (err) {
    console.error('Failed to load recent dispenses:', err);
  }
}

function debouncedLoad() {
  clearTimeout(timer);
  timer = setTimeout(loadPrescriptions, 300);
}

function selectPrescription(prescription) {
  // Navigate to dedicated details page instead of inline form
  router.push({ name: 'DispenseMedicineDetails', params: { prescriptionId: prescription.id } });
}

function onMedicineSelect() {
  selectedMedicine.value = availableMedicines.value.find(m => m.id === parseInt(dispenseForm.value.medicine));
  if (selectedMedicine.value) {
    dispenseForm.value.amount_charged = (selectedMedicine.value.selling_price * dispenseForm.value.quantity_dispensed).toFixed(2);
  }
}

async function dispense() {
  try {
    isLoading.value = true;
    error.value = '';

    if (!selectedMedicine.value) {
      error.value = 'Please select a medicine';
      return;
    }

    if (!currentInvoice.value || currentInvoice.value.status !== 'PAID') {
      error.value = 'Payment not approved. Dispensing requires a PAID invoice.';
      return;
    }

    if (dispenseForm.value.quantity_dispensed > selectedMedicine.value.current_stock) {
      error.value = `Insufficient stock. Available: ${selectedMedicine.value.current_stock}`;
      return;
    }

    const prescriptionId = dispenseForm.value.prescription;
    const medicineId = dispenseForm.value.medicine;
    const quantity = dispenseForm.value.quantity_dispensed;

    // Create a dispense record via backend API (handles stock deduction + status update)
    const { data } = await api.post('/api/pharmacy/dispense/', {
      prescription: prescriptionId,
      medicine: medicineId,
      quantity_dispensed: quantity,
      amount_charged: dispenseForm.value.amount_charged,
      notes: dispenseForm.value.notes || `Dispensed via frontend by ${localStorage.getItem('username') || 'pharmacist'}`,
    });

    // Update UI inline with returned current_stock
    if (typeof data?.medicine_current_stock === 'number') {
      selectedMedicine.value.current_stock = data.medicine_current_stock;
      const idx = availableMedicines.value.findIndex(m => m.id === selectedMedicine.value.id);
      if (idx !== -1) availableMedicines.value[idx].current_stock = data.medicine_current_stock;
    } else {
      // Fallback: decrement locally
      selectedMedicine.value.current_stock = Math.max(0, selectedMedicine.value.current_stock - quantity);
    }

    // Print receipt
    const win = window.open('', '_blank', 'width=480,height=640');
    const html = `
      <html>
        <head><title>Prescription Receipt</title></head>
        <body>
          <h2>Prescription Receipt</h2>
          <div>Patient: ${selectedPrescription.value.patient.name}</div>
          <div>Medicine: ${selectedMedicine.value.name}</div>
          <div>Quantity: ${quantity}</div>
          <div>Amount Charged: Kshs ${dispenseForm.value.amount_charged}</div>
          <div>Dispensed By: ${localStorage.getItem('username') || 'pharmacist'}</div>
          <div>Date/Time: ${new Date().toLocaleString()}</div>
          <button onclick="window.print()">Print</button>
        </body>
      </html>`;
    win.document.write(html);
    win.document.close();

    alert('Prescription dispensed and stock updated successfully!');
    cancelDispense();
    await Promise.all([loadPrescriptions(), loadMedicines(), loadRecentDispenses()]);
  } catch (err) {
    const data = err.response?.data || {};
    error.value = data.prescription || data.detail || data.medicine?.[0] || data.non_field_errors?.[0] || 'Failed to dispense prescription';
  } finally {
    isLoading.value = false;
  }
}

async function generateInvoice() {
  try {
    isLoading.value = true;
    error.value = '';
    if (!selectedPrescription.value || !selectedMedicine.value) {
      error.value = 'Select a prescription and medicine first';
      return;
    }
    const quantity = dispenseForm.value.quantity_dispensed || 1;
    const { data } = await api.post('/api/invoices/create_for_prescription/', {
      prescription: selectedPrescription.value.id,
      medicine: selectedMedicine.value.id,
      quantity
    });
    currentInvoice.value = data;
    alert(`Invoice #${data.id} created. Status: ${data.status}`);
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create invoice';
  } finally {
    isLoading.value = false;
  }
}

async function loadInvoiceForPrescription() {
  try {
    if (!selectedPrescription.value) return;
    const { data } = await api.get('/api/invoices/');
    currentInvoice.value = (data || []).find(inv => inv.prescription === selectedPrescription.value.id) || null;
  } catch (e) {
    console.warn('Failed to load invoice for prescription:', e);
  }
}

async function recordPayment() {
  try {
    isLoading.value = true;
    error.value = '';
    if (!currentInvoice.value) {
      error.value = 'No invoice found. Generate invoice first';
      return;
    }
    const amount = currentInvoice.value.total ?? ((selectedMedicine.value?.selling_price || 0) * (dispenseForm.value.quantity_dispensed || 1));
    const payload = {
      invoice: currentInvoice.value.id,
      amount,
      method: 'CASH',
      reference: `RCPT-${currentInvoice.value.id}`
    };
    await api.post('/api/payments/', payload);
    await loadInvoiceForPrescription();
    alert(`Payment recorded. Invoice #${currentInvoice.value?.id} status: ${currentInvoice.value?.status}`);
  } catch (e) {
    const data = e.response?.data || {};
    error.value = data.detail || data.non_field_errors?.[0] || 'Failed to record payment';
  } finally {
    isLoading.value = false;
  }
}

function cancelDispense() {
  selectedPrescription.value = null;
  selectedMedicine.value = null;
  currentInvoice.value = null;
  dispenseForm.value = {
    prescription: '',
    medicine: '',
    quantity_dispensed: 1,
    amount_charged: 0,
    notes: ''
  };
  error.value = '';
}

function getStatusBadge(status) {
  const styles = {
    PENDING: 'padding: 5px 10px; background: #fdcb6e; color: #333; border-radius: 4px; font-size: 0.85em;',
    DISPENSED: 'padding: 5px 10px; background: #00b894; color: white; border-radius: 4px; font-size: 0.85em;',
    COMPLETED: 'padding: 5px 10px; background: #636e72; color: white; border-radius: 4px; font-size: 0.85em;',
    DUE: 'padding: 5px 10px; background: #ff7675; color: white; border-radius: 4px; font-size: 0.85em;',
    PAID: 'padding: 5px 10px; background: #00b894; color: white; border-radius: 4px; font-size: 0.85em;',
    VOID: 'padding: 5px 10px; background: #b2bec3; color: #2d3436; border-radius: 4px; font-size: 0.85em;'
  };
  return styles[status] || '';
}

onMounted(() => {
  loadPrescriptions();
  loadMedicines();
  loadRecentDispenses();
});
</script>

<style scoped>
label { display: block; margin-bottom: 5px; font-weight: bold; }
input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.btn { padding: 10px 20px; background: #0984e3; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; }
.btn-secondary { background: #636e72; }
.btn:hover { opacity: 0.9; }
.prescription-card { padding: 15px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; }
.info-box { padding: 15px; background: #e3f2fd; border-left: 4px solid #0984e3; border-radius: 4px; }
</style>
