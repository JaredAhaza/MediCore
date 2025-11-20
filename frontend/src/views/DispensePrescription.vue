<template>
  <div>
    <div class="card">
      <h3>Dispense Prescription</h3>
      <p>Dispense medicine to patients with active prescriptions</p>
    </div>

    <div class="card">
      <h4>Select Prescription</h4>
      <div style="margin-bottom: 20px;">
        <input v-model="searchQuery" placeholder="Search by patient name, prescription or national ID..." @input="debouncedLoad" />
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
            <div v-if="prescription.patient?.national_id" style="font-size:0.85em; color:#2d3436;">
              National ID: {{ prescription.patient.national_id }}
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

          <div class="grid-two">
            <div>
              <label>Discount (Kshs)</label>
              <input v-model.number="dispenseForm.discount_amount" type="number" step="0.01" min="0" />
            </div>
            <div>
              <label>Additional Charges (Kshs)</label>
              <input v-model.number="dispenseForm.additional_charges" type="number" step="0.01" min="0" />
            </div>
          </div>

          <div v-if="hasAdditionalCharges" style="margin-top: 10px; padding: 12px; background: #fff3cd; border-radius: 4px; border-left: 4px solid #f39c12;">
            <label style="font-weight: 600; color: #856404;">
              Additional Charge Note (e.g., Packaging costs) *
            </label>
            <input 
              v-model.trim="dispenseForm.additional_note" 
              type="text" 
              maxlength="120" 
              placeholder="e.g. Packaging costs" 
              required
              style="border: 2px solid #0984e3; margin-top: 6px; width: 100%; padding: 8px;"
            />
            <small style="color: #666; display: block; margin-top: 4px;">
              This note will appear on receipts and invoices
            </small>
            <div v-if="showAdditionalNoteWarning" style="color: #ff7675; font-size: 0.85em; margin-top: 4px; font-weight: 500;">
              ⚠ Please enter a note for the additional charges
            </div>
          </div>

          <div class="info-box total-box">
            <div>
              <strong>Final Amount:</strong> Kshs {{ formatMoney(finalAmount) }}
            </div>
            <div style="font-size: 0.9em; margin-top: 8px; color: #555;">
              <div>Amount Charged: Kshs {{ formatMoney(dispenseForm.amount_charged) }}</div>
              <div v-if="dispenseForm.discount_amount > 0">
                Discount: -Kshs {{ formatMoney(dispenseForm.discount_amount) }}
              </div>
              <div v-if="dispenseForm.additional_charges > 0">
                Additional Charges: +Kshs {{ formatMoney(dispenseForm.additional_charges) }}
                <span v-if="dispenseForm.additional_note" style="color: #0984e3; font-style: italic; font-weight: 500;">
                  ({{ dispenseForm.additional_note }})
                </span>
                <span v-else style="color: #ff7675; font-size: 0.85em;">
                  — Note required
                </span>
              </div>
            </div>
            <small style="display: block; margin-top: 8px;">Final = Amount charged - Discount + Additional charges</small>
          </div>

          <div>
            <label>Notes</label>
            <textarea v-model="dispenseForm.notes" rows="3" placeholder="Optional notes"></textarea>
          </div>

          <div class="payment-config">
            <div>
              <label>Payment Method</label>
              <select v-model="paymentForm.method">
                <option v-for="method in paymentMethods" :key="method.value" :value="method.value">
                  {{ method.label }}
                </option>
              </select>
            </div>
            <div v-if="paymentRequiresReference">
              <label>Reference *</label>
              <input
                v-model.trim="paymentForm.reference"
                placeholder="e.g. MPESA code / transaction id"
              />
            </div>
          </div>

          <div style="display: flex; gap: 10px; align-items: center;">
            <button type="submit" class="btn" :disabled="isLoading || !currentInvoice || currentInvoice.status !== 'PAID'">{{ isLoading ? 'Processing...' : 'Complete Dispensing' }}</button>
            <button type="button" @click="cancelDispense" class="btn btn-secondary" :disabled="isLoading">Cancel</button>
            <button type="button" class="btn" style="background:#00b894;" @click="generateInvoice" :disabled="isLoading || !selectedMedicine">Generate Invoice</button>
            <button
              type="button"
              class="btn"
              style="background:#6c5ce7;"
              @click="recordPayment"
              :disabled="isLoading || !currentInvoice || paymentReferenceMissing"
            >
              Record Payment
            </button>
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
            <div v-if="currentInvoice.services && currentInvoice.services.length" class="invoice-services">
              <div style="font-weight:600; margin-top:8px;">Line Items</div>
              <ul>
                <li v-for="(svc, idx) in currentInvoice.services" :key="idx">
                  {{ svc.name }} — Kshs {{ formatMoney(svc.amount) }}
                </li>
              </ul>
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
              Qty: {{ disp.quantity_dispensed }} • Kshs {{ formatMoney(disp.final_amount ?? disp.amount_charged) }}
          </div>
        </div>
        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
          {{ new Date(disp.dispensed_at).toLocaleString() }} • By: {{ disp.pharmacist_name }}
          <span v-if="disp.additional_charges_note"> • Note: {{ disp.additional_charges_note }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
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

const paymentForm = ref({
  method: 'CASH',
  reference: '',
});
const paymentMethods = [
  { value: 'CASH', label: 'Cash' },
  { value: 'MPESA', label: 'Mpesa' },
  { value: 'CARD', label: 'Card' },
  { value: 'INSURANCE', label: 'Insurance' },
];
const paymentRequiresReference = computed(() => paymentForm.value.method !== 'CASH');
const paymentReferenceMissing = computed(() => paymentRequiresReference.value && !paymentForm.value.reference?.trim());

const dispenseForm = ref({
  prescription: '',
  medicine: '',
  quantity_dispensed: 1,
  amount_charged: 0,
  discount_amount: 0,
  additional_charges: 0,
  additional_note: '',
  notes: ''
});

const finalAmount = computed(() => {
  const base = Number(dispenseForm.value.amount_charged || 0);
  const discount = Number(dispenseForm.value.discount_amount || 0);
  const extra = Number(dispenseForm.value.additional_charges || 0);
  const net = base - discount + extra;
  return net > 0 ? Number(net.toFixed(2)) : 0;
});

const hasAdditionalCharges = computed(() => {
  return Number(dispenseForm.value.additional_charges || 0) > 0;
});

const showAdditionalNoteWarning = computed(() => {
  return hasAdditionalCharges.value && !dispenseForm.value.additional_note?.trim();
});

function formatMoney(val) {
  const num = Number(val || 0);
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

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
    dispenseForm.value.amount_charged = Number((selectedMedicine.value.selling_price * dispenseForm.value.quantity_dispensed).toFixed(2));
    dispenseForm.value.discount_amount = 0;
    dispenseForm.value.additional_charges = 0;
    dispenseForm.value.additional_note = '';
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

    if (finalAmount.value < 0) {
      error.value = 'Final amount cannot be negative';
      return;
    }

    // Create a dispense record via backend API (handles stock deduction + status update)
    const { data } = await api.post('/api/pharmacy/dispense/', {
      prescription: prescriptionId,
      medicine: medicineId,
      quantity_dispensed: quantity,
      amount_charged: dispenseForm.value.amount_charged,
      discount_amount: dispenseForm.value.discount_amount,
      additional_charges: dispenseForm.value.additional_charges,
      additional_charges_note: dispenseForm.value.additional_note,
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
    const win = window.open('', '_blank', 'width=520,height=720');
    const pharmacistUsername = data?.pharmacist_username || localStorage.getItem('username') || 'pharmacist';
    const pharmacistId = data?.pharmacist_id || '';
    const patientName = data?.patient_name || selectedPrescription.value?.patient?.name || currentInvoice.value?.patient_detail?.name || 'Unknown Patient';
    const paymentStatus = currentInvoice.value?.status || 'N/A';
    const goodsAmount = dispenseForm.value.amount_charged;
    const discountAmount = dispenseForm.value.discount_amount || 0;
    const additionalCharges = dispenseForm.value.additional_charges || 0;
    const finalTotal = finalAmount.value;
    const paymentMethodCode = paymentForm.value.method || 'CASH';
    const methodLabels = { CASH: 'Cash', MPESA: 'Mpesa', CARD: 'Card', INSURANCE: 'Insurance' };
    const paymentMethodLabel = methodLabels[paymentMethodCode] || paymentMethodCode;
    const paymentReference = (paymentForm.value.reference || '').trim() || (paymentMethodCode === 'CASH' ? '-' : '');
    
    const html = `
      <html>
        <head><title>Prescription Receipt</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2 style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;">Prescription Receipt</h2>
          
          <div style="margin-bottom: 20px;">
            <div style="margin: 10px 0;"><strong>Patient:</strong> ${patientName}</div>
            <div style="margin: 10px 0;"><strong>Medicine:</strong> ${selectedMedicine.value.name}</div>
            <div style="margin: 10px 0;"><strong>Quantity:</strong> ${quantity}</div>
          </div>
          
          <hr style="margin: 20px 0; border: 1px solid #ddd;">
          
          <div style="margin-bottom: 20px;">
            <h3 style="margin: 0 0 15px 0; font-size: 1.1em;">Cost Breakdown</h3>
            <div style="display: flex; justify-content: space-between; margin: 8px 0; padding: 5px 0;">
              <span>Goods/Medicine Charge:</span>
              <span><strong>Kshs ${formatMoney(goodsAmount)}</strong></span>
            </div>
            ${discountAmount > 0 ? `
            <div style="display: flex; justify-content: space-between; margin: 8px 0; padding: 5px 0; color: #00b894;">
              <span>Discount:</span>
              <span><strong>-Kshs ${formatMoney(discountAmount)}</strong></span>
            </div>
            ` : ''}
            ${additionalCharges > 0 ? `
            <div style="display: flex; justify-content: space-between; margin: 8px 0; padding: 5px 0; color: #0984e3;">
              <span>Additional Charges${dispenseForm.value.additional_note ? ` (${dispenseForm.value.additional_note})` : ''}:</span>
              <span><strong>+Kshs ${formatMoney(additionalCharges)}</strong></span>
            </div>
            ` : ''}
            <hr style="margin: 15px 0; border: 1px solid #ddd;">
            <div style="display: flex; justify-content: space-between; margin: 10px 0; padding: 10px 0; font-size: 1.2em; border-top: 2px solid #333; border-bottom: 2px solid #333;">
              <span><strong>Total Amount:</strong></span>
              <span><strong>Kshs ${formatMoney(finalTotal)}</strong></span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 10px 0; padding: 5px 0;">
              <span><strong>Payment Status:</strong></span>
              <span style="color: ${paymentStatus === 'PAID' ? '#00b894' : paymentStatus === 'DUE' ? '#ff7675' : '#636e72'}; font-weight: bold;">
                ${paymentStatus}
              </span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 6px 0; padding: 4px 0; font-size: 0.95em;">
              <span><strong>Payment Method:</strong></span>
              <span>${paymentMethodLabel}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 4px 0; padding: 4px 0; font-size: 0.9em;">
              <span><strong>Reference:</strong></span>
              <span>${paymentReference}</span>
            </div>
          </div>
          
          <hr style="margin: 20px 0; border: 1px solid #ddd;">
          
          <div style="margin-top: 20px; font-size: 0.9em; color: #666;">
            <div style="margin: 8px 0;"><strong>Dispensed By:</strong> ${pharmacistUsername}${pharmacistId ? ` (ID: ${pharmacistId})` : ''}</div>
            <div style="margin: 8px 0;"><strong>Date/Time:</strong> ${new Date().toLocaleString()}</div>
          </div>
          
          <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #0984e3; color: white; border: none; border-radius: 4px;">Print</button>
          </div>
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
      quantity,
      discount: dispenseForm.value.discount_amount,
      additional_charges: dispenseForm.value.additional_charges,
      additional_label: dispenseForm.value.additional_note
    });
    currentInvoice.value = data;
    // Show invoice receipt with details
    const win = window.open('', '_blank', 'width=520,height=720');
    const itemsHtml = (data.services || []).map(s => `<li style="margin: 5px 0;">${s.name} — Kshs ${formatMoney(s.amount)}</li>`).join('');
    const patientName = selectedPrescription.value?.patient?.name || data.patient_detail?.name || 'Unknown Patient';
    const createdByUsername = data.created_by_username || localStorage.getItem('username') || 'user';
    const createdById = data.created_by_id || '';
    const html = `
      <html><head><title>Invoice Receipt</title></head>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px;">Invoice #${data.id}</h2>
        <div style="margin: 15px 0;"><strong>Status:</strong> ${data.status}</div>
        <div style="margin: 15px 0;"><strong>Patient:</strong> ${patientName}</div>
        <hr style="margin: 20px 0;">
        <h3 style="margin: 15px 0;">Items</h3>
        <ul style="list-style: none; padding: 0;">${itemsHtml}</ul>
        <hr style="margin: 20px 0;">
        <div style="margin: 10px 0;">Subtotal: Kshs ${formatMoney(data.subtotal)}</div>
        <div style="margin: 10px 0;">Discount: Kshs ${formatMoney(data.discount)}</div>
        <div style="margin: 15px 0; font-size: 1.2em;"><strong>Total Due: Kshs ${formatMoney(data.total)}</strong></div>
        <hr style="margin: 20px 0;">
        <div style="margin: 10px 0;"><strong>Created By:</strong> ${createdByUsername}${createdById ? ` (ID: ${createdById})` : ''}</div>
        <div style="margin: 10px 0;"><strong>Date/Time:</strong> ${new Date(data.created_at).toLocaleString()}</div>
        <div style="text-align: center; margin-top: 30px;">
          <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #0984e3; color: white; border: none; border-radius: 4px;">Print</button>
        </div>
      </body></html>`;
    win.document.write(html);
    win.document.close();
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
    if (paymentReferenceMissing.value) {
      error.value = 'Please enter a payment reference.';
      return;
    }
    const amount = currentInvoice.value?.total ?? finalAmount.value;
    const payload = {
      invoice: currentInvoice.value.id,
      amount,
      method: paymentForm.value.method,
    };
    const ref = paymentForm.value.reference?.trim();
    if (ref) payload.reference = ref;
    else if (paymentForm.value.method !== 'CASH') payload.reference = '';
    await api.post('/api/payments/', payload);
    await loadInvoiceForPrescription();
    paymentForm.value.reference = '';
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
    discount_amount: 0,
    additional_charges: 0,
    additional_note: '',
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
.total-box { background: #ecfdf5; border-color: #0c9f6a; }
.grid-two { display:grid; gap:12px; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); }
.invoice-services ul { padding-left: 18px; margin: 6px 0 0; }
.invoice-services li { font-size: 0.9em; color: #333; margin-bottom: 2px; }
.payment-config {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit,minmax(180px,1fr));
}
</style>
