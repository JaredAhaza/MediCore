<template>
  <div>
    <div class="card">
      <h3>Dispense Medicine — Details</h3>
      <p>Review and confirm dispensing details. Fields are locked.</p>
    </div>

    <div class="card">
      <div class="info-box">
        <strong>Patient:</strong> {{ prescription?.patient?.name }}<br />
        <strong>Medication:</strong> {{ prescription?.medication }}<br />
        <strong>Dosage:</strong> {{ prescription?.dosage }} | <strong>Duration:</strong> {{ prescription?.duration }}
      </div>

      <div style="margin-top: 10px;">
        <label>Select Medicine from Inventory *</label>
        <select v-model="selectedMedicineId" @change="onMedicineSelect" :disabled="loading || locked">
          <option value="">Select Medicine</option>
          <option v-for="m in availableMedicines" :key="m.id" :value="m.id">
            {{ m.name }} (Stock: {{ m.current_stock }}) — Kshs {{ m.selling_price }}
          </option>
        </select>
      </div>

      <div v-if="selectedMedicine" class="info-box" style="background:#fff3cd; margin-top: 10px;">
        <strong>{{ selectedMedicine.name }}</strong><br />
        Available Stock: <strong>{{ selectedMedicine.current_stock }}</strong> • Selling Price: Kshs {{ selectedMedicine.selling_price }}
      </div>

      <form @submit.prevent="completeDispense" style="margin-top: 15px;">
        <div style="display:grid; gap:12px;">
          <div>
            <label>Quantity to Dispense</label>
            <input type="number" :value="form.quantity_dispensed" disabled />
          </div>
          <div>
            <label>Amount to Charge (Kshs)</label>
            <input type="number" :value="form.amount_charged" disabled />
          </div>
          <div class="grid-two">
            <div>
              <label>Discount (Kshs)</label>
              <input type="number" v-model.number="form.discount_amount" min="0" step="0.01" :disabled="loading" />
            </div>
            <div>
              <label>Additional Charges (Kshs)</label>
              <input type="number" v-model.number="form.additional_charges" min="0" step="0.01" :disabled="loading" />
            </div>
          </div>

          <div v-if="Number(form.additional_charges) > 0">
            <label>Additional Charge Note</label>
            <input type="text" v-model.trim="form.additional_note" maxlength="120" placeholder="e.g. Packaging costs" :disabled="loading" />
          </div>

          <div class="info-box total-box">
            <div><strong>Final Amount:</strong> Kshs {{ formatMoney(finalAmount) }}</div>
            <small>Final = Amount charged - Discount + Additional charges</small>
          </div>
          <div>
            <label>Notes</label>
            <textarea v-model="form.notes" rows="3" placeholder="Optional notes"></textarea>
          </div>

          <div v-if="currentInvoice" class="info-box" style="background:#f1f2f6;">
            <div>
              <strong>Invoice #{{ currentInvoice.id }}</strong> • Status:
              <span :style="badge(currentInvoice.status)">{{ currentInvoice.status }}</span>
            </div>
            <div style="font-size:0.9em; color:#555;">
              Subtotal: Kshs {{ currentInvoice.subtotal }} • Discount: Kshs {{ currentInvoice.discount }} • Total: Kshs {{ currentInvoice.total }}
            </div>
          </div>

          <div v-if="error" style="color:#d63031; padding:10px; background:#fee; border-radius:4px;">{{ error }}</div>

          <div style="display:flex; gap:10px; align-items:center;">
            <button type="button" class="btn" style="background:#00b894;" @click="generateInvoice" :disabled="loading || !selectedMedicine">Generate Invoice</button>
            <button type="button" class="btn" style="background:#6c5ce7;" @click="recordPayment" :disabled="loading || !currentInvoice">Record Payment</button>
            <button type="submit" class="btn" :disabled="loading || !currentInvoice || currentInvoice.status !== 'PAID'">Complete Dispensing</button>
            <button type="button" class="btn btn-secondary" @click="cancel" :disabled="loading">Cancel</button>
            <span v-if="loading" style="color:#666;">Processing…</span>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api/client';

const route = useRoute();
const router = useRouter();
const prescriptionId = Number(route.params.prescriptionId);

const prescription = ref(null);
const availableMedicines = ref([]);
const selectedMedicineId = ref('');
const selectedMedicine = computed(() => availableMedicines.value.find(m => m.id === Number(selectedMedicineId.value)) || null);
const currentInvoice = ref(null);
const error = ref('');
const loading = ref(false);
const locked = ref(false); // lock inputs after auto-fill

const form = ref({
  prescription: prescriptionId,
  medicine: '',
  quantity_dispensed: 1,
  amount_charged: 0,
  discount_amount: 0,
  additional_charges: 0,
  additional_note: '',
  notes: ''
});

const finalAmount = computed(() => {
  const base = Number(form.value.amount_charged || 0);
  const discount = Number(form.value.discount_amount || 0);
  const extra = Number(form.value.additional_charges || 0);
  const net = base - discount + extra;
  return net > 0 ? Number(net.toFixed(2)) : 0;
});

function formatMoney(val) {
  const num = Number(val || 0);
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function badge(status) {
  const styles = {
    DUE: 'padding:5px 10px; background:#ff7675; color:white; border-radius:4px; font-size:.85em;',
    PAID: 'padding:5px 10px; background:#00b894; color:white; border-radius:4px; font-size:.85em;',
    VOID: 'padding:5px 10px; background:#b2bec3; color:#2d3436; border-radius:4px; font-size:.85em;',
    PENDING: 'padding:5px 10px; background:#fdcb6e; color:#333; border-radius:4px; font-size:.85em;',
    DISPENSED: 'padding:5px 10px; background:#00b894; color:white; border-radius:4px; font-size:.85em;',
    COMPLETED: 'padding:5px 10px; background:#636e72; color:white; border-radius:4px; font-size:.85em;',
  };
  return styles[status] || '';
}

function extractNumber(text) {
  const m = String(text || '').match(/\d+/);
  return m ? Number(m[0]) : 1;
}

function calculateTotalQuantity(presc) {
  const dosageNum = extractNumber(presc.dosage);
  const durationNum = extractNumber(presc.duration);
  const freqMatch = String(presc.dosage || '').toLowerCase().match(/(once|twice|thrice|\d+)/);
  let freq = 1;
  if (freqMatch) {
    const f = freqMatch[1];
    if (f === 'once') freq = 1; else if (f === 'twice') freq = 2; else if (f === 'thrice') freq = 3; else freq = Number(f);
  }
  return dosageNum * freq * durationNum;
}

async function loadPrescription() {
  const { data } = await api.get(`/api/prescriptions/${prescriptionId}/`);
  prescription.value = data;
}

async function loadMedicines() {
  const { data } = await api.get('/api/pharmacy/medicines/', { params: { is_active: true } });
  availableMedicines.value = data.filter(m => m.current_stock > 0);
}

async function loadInvoice() {
  const { data } = await api.get('/api/invoices/');
  currentInvoice.value = (data || []).find(inv => inv.prescription === prescriptionId) || null;
}

function onMedicineSelect() {
  error.value = '';
  const med = selectedMedicine.value;
  if (!med) return;
  form.value.medicine = med.id;
  // Calculate quantity for tablet/capsule, otherwise default to 1
  const requiresCalc = ['TABLET', 'CAPSULE'].includes(med.category);
  const qty = requiresCalc ? calculateTotalQuantity(prescription.value) : 1;
  form.value.quantity_dispensed = qty;
  form.value.amount_charged = Number(((med.selling_price || 0) * qty).toFixed(2));
  form.value.discount_amount = 0;
  form.value.additional_charges = 0;
  form.value.additional_note = '';
  locked.value = true; // lock after auto-fill
}

async function generateInvoice() {
  try {
    loading.value = true;
    error.value = '';
    if (!prescription.value || !selectedMedicine.value) { error.value = 'Select a medicine first'; return; }
    const quantity = form.value.quantity_dispensed || 1;
    const { data } = await api.post('/api/invoices/create_for_prescription/', {
      prescription: prescriptionId,
      medicine: selectedMedicine.value.id,
      quantity,
      discount: form.value.discount_amount,
      additional_charges: form.value.additional_charges,
      additional_label: form.value.additional_note
    });
    currentInvoice.value = data;
    // Show invoice receipt with details
    const win = window.open('', '_blank', 'width=520,height=720');
    const itemsHtml = (data.services || []).map(s => `<li>${s.name} — Kshs ${s.amount}</li>`).join('');
    const html = `
      <html><head><title>Invoice Receipt</title></head><body>
        <h2>Invoice #${data.id}</h2>
        <div>Status: ${data.status}</div>
        <div>Patient: ${prescription.value?.patient?.name || ''}</div>
        <h3>Items</h3>
        <ul>${itemsHtml}</ul>
        <div>Subtotal: Kshs ${data.subtotal}</div>
        <div>Discount: Kshs ${data.discount}</div>
        <div><strong>Total Due: Kshs ${data.total}</strong></div>
        <button onclick="window.print()">Print</button>
      </body></html>`;
    win.document.write(html);
    win.document.close();
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to create invoice';
  } finally {
    loading.value = false;
  }
}

async function recordPayment() {
  try {
    loading.value = true;
    error.value = '';
    if (!currentInvoice.value) { error.value = 'No invoice found'; return; }
    const payload = {
      invoice: currentInvoice.value.id,
      amount: currentInvoice.value?.total ?? finalAmount.value,
      method: 'CASH',
      reference: `RCPT-${currentInvoice.value.id}`
    };
    await api.post('/api/payments/', payload);
    await loadInvoice();
    alert(`Payment recorded. Invoice #${currentInvoice.value?.id} status: ${currentInvoice.value?.status}`);
  } catch (e) {
    const data = e.response?.data || {};
    error.value = data.detail || data.non_field_errors?.[0] || 'Failed to record payment';
  } finally {
    loading.value = false;
  }
}

async function completeDispense() {
  try {
    loading.value = true;
    error.value = '';
    if (!selectedMedicine.value) { error.value = 'Select a medicine first'; return; }
    if (!currentInvoice.value || currentInvoice.value.status !== 'PAID') { error.value = 'Payment not approved. Requires PAID invoice.'; return; }
    if (finalAmount.value < 0) { error.value = 'Final amount cannot be negative'; return; }
    const payload = {
      prescription: prescriptionId,
      medicine: form.value.medicine,
      quantity_dispensed: form.value.quantity_dispensed,
      amount_charged: form.value.amount_charged,
      discount_amount: form.value.discount_amount,
      additional_charges: form.value.additional_charges,
      additional_charges_note: form.value.additional_note,
      notes: form.value.notes || `Dispensed via details page`
    };
    await api.post('/api/pharmacy/dispense/', payload);
    const win = window.open('', '_blank', 'width=520,height=720');
    if (win) {
      const html = `
        <html><head><title>Prescription Receipt</title></head><body>
          <h2>Prescription Receipt</h2>
          <div>Patient: ${prescription.value?.patient?.name || ''}</div>
          <div>Medicine: ${selectedMedicine.value?.name || ''}</div>
          <div>Quantity: ${form.value.quantity_dispensed}</div>
          <div>Amount Charged: Kshs ${formatMoney(form.value.amount_charged)}</div>
          <div>Discount: Kshs ${formatMoney(form.value.discount_amount)}</div>
          <div>Additional Charges: Kshs ${formatMoney(form.value.additional_charges)}</div>
          ${form.value.additional_note ? `<div>Note: ${form.value.additional_note}</div>` : ''}
          <div><strong>Final Amount: Kshs ${formatMoney(finalAmount.value)}</strong></div>
          <div>Dispensed By: ${localStorage.getItem('username') || 'pharmacist'}</div>
          <div>Date/Time: ${new Date().toLocaleString()}</div>
          <button onclick="window.print()">Print</button>
        </body></html>`;
      win.document.write(html);
      win.document.close();
    }
    alert('Prescription dispensed successfully.');
    router.push({ name: 'DispensePrescription' });
  } catch (e) {
    const data = e.response?.data || {};
    error.value = data.prescription || data.detail || data.medicine?.[0] || data.non_field_errors?.[0] || 'Failed to dispense prescription';
  } finally {
    loading.value = false;
  }
}

function cancel() {
  router.push({ name: 'DispensePrescription' });
}

onMounted(async () => {
  await loadPrescription();
  await loadMedicines();
  await loadInvoice();
});
</script>

<style scoped>
label { display:block; margin-bottom:5px; font-weight:bold; }
input, select, textarea { width:100%; padding:8px; border:1px solid #ddd; border-radius:4px; }
.btn { padding:10px 20px; background:#0984e3; color:white; text-decoration:none; border-radius:4px; border:none; cursor:pointer; }
.btn-secondary { background:#636e72; }
.btn:hover { opacity:0.9; }
.info-box { padding:15px; background:#e3f2fd; border-left:4px solid #0984e3; border-radius:4px; }
.total-box { background:#ecfdf5; border-color:#0c9f6a; }
.grid-two { display:grid; gap:12px; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); }
.card { padding:15px; border:1px solid #ddd; border-radius:4px; margin-bottom:10px; }
</style>