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
            Unit Price: ${{ selectedMedicine.unit_price }}
          </div>

          <div>
            <label>Quantity to Dispense *</label>
            <input v-model.number="dispenseForm.quantity_dispensed" type="number" min="1" required />
          </div>

          <div>
            <label>Amount to Charge ($) *</label>
            <input v-model.number="dispenseForm.amount_charged" type="number" step="0.01" min="0" required />
            <small v-if="selectedMedicine" style="color: #666;">
              Suggested: ${{ (selectedMedicine.unit_price * dispenseForm.quantity_dispensed).toFixed(2) }}
            </small>
          </div>

          <div>
            <label>Notes</label>
            <textarea v-model="dispenseForm.notes" rows="3" placeholder="Optional notes"></textarea>
          </div>

          <div style="display: flex; gap: 10px;">
            <button type="submit" class="btn">Complete Dispensing</button>
            <button type="button" @click="cancelDispense" class="btn btn-secondary">Cancel</button>
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
            Qty: {{ disp.quantity_dispensed }} • ${{ disp.amount_charged }}
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
import { ref, computed, onMounted } from 'vue';
import api from '../api/client';

const prescriptions = ref([]);
const availableMedicines = ref([]);
const recentDispenses = ref([]);
const selectedPrescription = ref(null);
const selectedMedicine = ref(null);
const searchQuery = ref('');
const error = ref('');
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
  selectedPrescription.value = prescription;
  dispenseForm.value.prescription = prescription.id;
  error.value = '';
}

function onMedicineSelect() {
  selectedMedicine.value = availableMedicines.value.find(m => m.id === parseInt(dispenseForm.value.medicine));
  if (selectedMedicine.value) {
    dispenseForm.value.amount_charged = (selectedMedicine.value.unit_price * dispenseForm.value.quantity_dispensed).toFixed(2);
  }
}

async function dispense() {
  try {
    error.value = '';
    
    if (!selectedMedicine.value) {
      error.value = 'Please select a medicine';
      return;
    }
    
    if (dispenseForm.value.quantity_dispensed > selectedMedicine.value.current_stock) {
      error.value = `Insufficient stock. Available: ${selectedMedicine.value.current_stock}`;
      return;
    }
    
    await api.post('/api/pharmacy/dispense/', dispenseForm.value);
    
    alert('Prescription dispensed successfully!');
    cancelDispense();
    await Promise.all([loadPrescriptions(), loadMedicines(), loadRecentDispenses()]);
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to dispense prescription';
  }
}

function cancelDispense() {
  selectedPrescription.value = null;
  selectedMedicine.value = null;
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
    COMPLETED: 'padding: 5px 10px; background: #636e72; color: white; border-radius: 4px; font-size: 0.85em;'
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
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
input, select, textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.btn {
  padding: 10px 20px;
  background: #0984e3;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}
.btn-secondary {
  background: #636e72;
}
.btn:hover {
  opacity: 0.9;
}
.prescription-card {
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
}
.info-box {
  padding: 15px;
  background: #e3f2fd;
  border-left: 4px solid #0984e3;
  border-radius: 4px;
}
</style>
