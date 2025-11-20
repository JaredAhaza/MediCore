<template>
  <div>
    <div class="card">
      <h3>Dispense Medicine — Details</h3>
      <p>Review and confirm dispensing details. Fields are locked.</p>
    </div>

    <div class="card">
      <div class="info-box">
        <div><strong>Patient:</strong> {{ prescription?.patient?.name }}</div>
        <div v-if="prescription?.patient?.national_id">
          <strong>National ID:</strong> {{ prescription.patient.national_id }}
        </div>
        <div><strong>Medication:</strong> {{ prescription?.medication }}</div>
        <div><strong>Dosage:</strong> {{ prescription?.dosage }} | <strong>Duration:</strong> {{ prescription?.duration }}</div>
      </div>

      <SearchableSelect
        v-model="selectedMedicineOption"
        label="Select Medicine from Inventory *"
        :fetcher="fetchMedicines"
        :required="true"
        :disabled="loading || locked"
        placeholder="Search by medicine name, SKU or barcode"
        hint="Only active medicines with stock available are shown"
      />

      <div v-if="selectedMedicine" class="info-box" style="background:#fff3cd; margin-top: 10px;">
        <strong>{{ selectedMedicine.name }}</strong><br />
        Available Stock: <strong>{{ selectedMedicine.current_stock }}</strong> • Selling Price: Kshs {{ selectedMedicine.selling_price }}
        <div v-if="selectedMedicineOption?.meta" style="font-size:0.85em; color:#555; margin-top:4px;">
          {{ selectedMedicineOption.meta }}
        </div>
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

          <div v-if="hasAdditionalCharges" style="margin-top: 10px; padding: 12px; background: #fff3cd; border-radius: 4px; border-left: 4px solid #f39c12;">
            <label style="font-weight: 600; color: #856404;">
              Additional Charge Note (e.g., Packaging costs) *
            </label>
            <input 
              type="text" 
              v-model.trim="form.additional_note" 
              maxlength="120" 
              placeholder="e.g. Packaging costs" 
              :disabled="loading"
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
            <div><strong>Final Amount:</strong> Kshs {{ formatMoney(finalAmount) }}</div>
            <div style="font-size: 0.9em; margin-top: 8px; color: #555;">
              <div>Amount Charged: Kshs {{ formatMoney(form.amount_charged) }}</div>
              <div v-if="form.discount_amount > 0">
                Discount: -Kshs {{ formatMoney(form.discount_amount) }}
              </div>
              <div v-if="form.additional_charges > 0">
                Additional Charges: +Kshs {{ formatMoney(form.additional_charges) }}
                <span v-if="form.additional_note" style="color: #0984e3; font-style: italic; font-weight: 500;">
                  ({{ form.additional_note }})
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
            <textarea v-model="form.notes" rows="3" placeholder="Optional notes"></textarea>
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

          <div v-if="currentInvoice" class="info-box" style="background:#f1f2f6;">
            <div>
              <strong>Invoice #{{ currentInvoice.id }}</strong> • Status:
              <span :style="badge(currentInvoice.status)">{{ currentInvoice.status }}</span>
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

          <div v-if="error" style="color:#d63031; padding:10px; background:#fee; border-radius:4px;">{{ error }}</div>

          <div style="display:flex; gap:10px; align-items:center;">
            <button type="button" class="btn" style="background:#00b894;" @click="generateInvoice" :disabled="loading || !selectedMedicine">Generate Invoice</button>
            <button
              type="button"
              class="btn"
              style="background:#6c5ce7;"
              @click="recordPayment"
              :disabled="loading || !currentInvoice || paymentReferenceMissing"
            >
              Record Payment
            </button>
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
import SearchableSelect from '@/components/SearchableSelect.vue';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api/client';

const route = useRoute();
const router = useRouter();
const prescriptionId = Number(route.params.prescriptionId);

const prescription = ref(null);
const selectedMedicineOption = ref(null);
const selectedMedicine = computed(() => selectedMedicineOption.value?.raw || null);
const currentInvoice = ref(null);
const error = ref('');
const loading = ref(false);
const locked = ref(false); // lock inputs after auto-fill
const paymentForm = ref({
  method: 'CASH',
  reference: '',
});
const paymentRequiresReference = computed(() => paymentForm.value.method !== 'CASH');
const paymentReferenceMissing = computed(() => paymentRequiresReference.value && !paymentForm.value.reference?.trim());
const paymentMethods = [
  { value: 'CASH', label: 'Cash' },
  { value: 'MPESA', label: 'Mpesa' },
  { value: 'CARD', label: 'Card' },
  { value: 'INSURANCE', label: 'Insurance' },
];

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

const hasAdditionalCharges = computed(() => {
  return Number(form.value.additional_charges || 0) > 0;
});

const showAdditionalNoteWarning = computed(() => {
  return hasAdditionalCharges.value && !form.value.additional_note?.trim();
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

async function loadInvoice() {
  const { data } = await api.get('/api/invoices/');
  currentInvoice.value = (data || []).find(inv => inv.prescription === prescriptionId) || null;
}

watch(selectedMedicine, (med) => {
  if (!med) {
    form.value.medicine = '';
    locked.value = false;
    return;
  }
  autoFillFromMedicine(med);
});

function autoFillFromMedicine(med) {
  error.value = '';
  form.value.medicine = med.id;
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
    const itemsHtml = (data.services || []).map(s => `<li style="margin: 5px 0;">${s.name} — Kshs ${formatMoney(s.amount)}</li>`).join('');
    const patientName = prescription.value?.patient?.name || data.patient_detail?.name || 'Unknown Patient';
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
    if (paymentReferenceMissing.value) {
      error.value = 'Please enter a payment reference.';
      return;
    }
    const payload = {
      invoice: currentInvoice.value.id,
      amount: currentInvoice.value?.total ?? finalAmount.value,
      method: paymentForm.value.method,
    };
    const ref = paymentForm.value.reference?.trim();
    if (ref) payload.reference = ref;
    else if (paymentForm.value.method !== 'CASH') payload.reference = '';
    await api.post('/api/payments/', payload);
    await loadInvoice();
    paymentForm.value.reference = '';
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
    const { data: dispenseData } = await api.post('/api/pharmacy/dispense/', payload);
    const win = window.open('', '_blank', 'width=520,height=720');
    if (win) {
      const pharmacistUsername = dispenseData?.pharmacist_username || localStorage.getItem('username') || 'pharmacist';
      const pharmacistId = dispenseData?.pharmacist_id || '';
      const patientName = dispenseData?.patient_name || prescription.value?.patient?.name || currentInvoice.value?.patient_detail?.name || 'Unknown Patient';
      const paymentStatus = currentInvoice.value?.status || 'N/A';
      const goodsAmount = form.value.amount_charged;
      const discountAmount = form.value.discount_amount || 0;
      const additionalCharges = form.value.additional_charges || 0;
      const finalTotal = finalAmount.value;
      const paymentMethodCode = paymentForm.value.method || 'CASH';
      const methodLabels = { CASH: 'Cash', MPESA: 'Mpesa', CARD: 'Card', INSURANCE: 'Insurance' };
      const paymentMethodLabel = methodLabels[paymentMethodCode] || paymentMethodCode;
      const paymentReference = (paymentForm.value.reference || '').trim() || (paymentMethodCode === 'CASH' ? '-' : '');
      
      const html = `
        <html><head><title>Prescription Receipt</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2 style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;">Prescription Receipt</h2>
          
          <div style="margin-bottom: 20px;">
            <div style="margin: 10px 0;"><strong>Patient:</strong> ${patientName}</div>
            <div style="margin: 10px 0;"><strong>Medicine:</strong> ${selectedMedicine.value?.name || ''}</div>
            <div style="margin: 10px 0;"><strong>Quantity:</strong> ${form.value.quantity_dispensed}</div>
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
              <span>Additional Charges${form.value.additional_note ? ` (${form.value.additional_note})` : ''}:</span>
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

async function fetchMedicines(search = '', cursor = null) {
  const params = { is_active: true };
  if (search) params.search = search;
  if (cursor) params.cursor = cursor;
  const { data } = await api.get('/api/pharmacy/medicines/', { params });
  const { list, nextCursor } = normalizePaginated(data);
  const filtered = list.filter(m => Number(m.current_stock ?? 0) > 0);
  const items = filtered.map(mapMedicineOption);
  return { items, nextCursor };
}

function mapMedicineOption(medicine) {
  return {
    id: medicine.id,
    label: medicine.name,
    subtitle: `Stock: ${medicine.current_stock ?? 0} • Kshs ${formatMoney(medicine.selling_price || 0)}`,
    meta: [
      medicine.category ? `Category: ${medicine.category}` : null,
      medicine.sku ? `SKU: ${medicine.sku}` : null,
      medicine.barcode ? `Barcode: ${medicine.barcode}` : null,
    ].filter(Boolean).join(' • '),
    raw: medicine,
  };
}

function normalizePaginated(payload) {
  if (Array.isArray(payload)) return { list: payload, nextCursor: null };
  if (payload && Array.isArray(payload.results)) {
    return { list: payload.results, nextCursor: payload.next || payload.nextCursor || null };
  }
  if (payload && Array.isArray(payload.items)) {
    return { list: payload.items, nextCursor: payload.nextCursor || payload.next || null };
  }
  return { list: [], nextCursor: null };
}

onMounted(async () => {
  await loadPrescription();
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
.invoice-services ul { padding-left: 18px; margin: 6px 0 0; }
.invoice-services li { font-size: 0.9em; color: #333; margin-bottom: 2px; }
.grid-two { display:grid; gap:12px; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); }
.card { padding:15px; border:1px solid #ddd; border-radius:4px; margin-bottom:10px; }
.payment-config {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit,minmax(180px,1fr));
  margin-top: 8px;
}
</style>