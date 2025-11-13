<template>
  <div class="card" style="margin-top: 16px">
    <h3>Vendor Invoice Import</h3>
    <div style="color:#666; font-size:.9em; margin-bottom:8px;">
      Upload a CSV/TXT or a scanned invoice. We’ll extract lines, match medicines, and let you apply stock-in updates.
    </div>

    <div style="display:flex; gap:8px; align-items:center; margin-bottom:12px;">
      <input type="file" @change="onFile" accept=".csv,.txt,image/*,application/pdf" />
      <button class="btn" :disabled="loading || !file" @click="parse">Parse Invoice</button>
      <span v-if="loading" style="color:#888;">Processing…</span>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="lines.length" style="margin-top:8px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong>Parsed Lines</strong>
        <div style="display:flex; gap:8px;">
          <button class="btn" :disabled="applying" @click="apply">Apply to Inventory</button>
          <span v-if="applying" style="color:#888;">Applying…</span>
        </div>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th style="width:22%">Name</th>
              <th style="width:10%">Quantity</th>
              <th style="width:14%">Buying Price</th>
              <th style="width:14%">Batch</th>
              <th style="width:14%">Expiry</th>
              <th style="width:26%">Match Medicine</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(l, idx) in lines" :key="idx">
              <td>{{ l.name }}</td>
              <td>
                <input type="number" min="0" v-model.number="l.quantity" style="width:90px" />
              </td>
              <td>
                <input type="text" v-model="l.buying_price" style="width:110px" />
              </td>
              <td>
                <input type="text" v-model="l.batch_number" style="width:120px" />
              </td>
              <td>
                <input type="date" v-model="l.expiry_date" style="width:140px" />
              </td>
              <td>
                <div v-if="l.match">
                  <div style="display:flex; gap:6px; align-items:center;">
                    <span class="pill">{{ l.match.name }}</span>
                    <button class="btn small" @click="l.match=null">Change</button>
                  </div>
                </div>
                <div v-else>
                  <input type="text" v-model="l.search" @input="onSearch(idx)" placeholder="Search medicine…" />
                  <div v-if="l.options && l.options.length" class="dropdown">
                    <div v-for="opt in l.options" :key="opt.id" class="dropdown-item" @click="selectMatch(idx, opt)">
                      {{ opt.name }}
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="result" class="success" style="margin-top:8px;">
        Applied: {{ result.created_count }} transaction(s)
        <span v-if="result.price_updates && result.price_updates.length"> · Updated prices for {{ result.price_updates.length }} medicine(s)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import client from '@/api/client';

const file = ref(null);
const lines = ref([]);
const loading = ref(false);
const error = ref('');
const applying = ref(false);
const result = ref(null);

function onFile(e) {
  error.value = '';
  result.value = null;
  const f = e.target.files && e.target.files[0];
  file.value = f || null;
}

async function parse() {
  if (!file.value) return;
  loading.value = true;
  error.value = '';
  lines.value = [];
  try {
    const form = new FormData();
    form.append('file', file.value);
    const { data } = await client.post('/api/pharmacy/inventory-transactions/parse_invoice/', form);
    lines.value = (data && data.lines) ? data.lines.map(l => ({ ...l, search: '', options: [] })) : [];
    if (!lines.value.length) error.value = 'No lines parsed. Ensure CSV/TXT with columns: name,quantity,buying_price,batch,expiry or configure OCR.';
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Failed to parse invoice.';
  } finally {
    loading.value = false;
  }
}

async function onSearch(idx) {
  const q = (lines.value[idx].search || '').trim();
  if (!q) { lines.value[idx].options = []; return; }
  try {
    const { data } = await client.get(`/api/pharmacy/medicines/?search=${encodeURIComponent(q)}`);
    const opts = (data || []).map(m => ({ id: m.id, name: m.name }));
    lines.value[idx].options = opts;
  } catch (e) {
    lines.value[idx].options = [];
  }
}

function selectMatch(idx, opt) {
  lines.value[idx].match = opt;
  lines.value[idx].options = [];
  lines.value[idx].search = '';
}

async function apply() {
  applying.value = true;
  error.value = '';
  result.value = null;
  try {
    const payload = {
      lines: lines.value
        .filter(l => l.match && (l.quantity || 0) > 0)
        .map(l => ({
          medicine: l.match.id,
          quantity: l.quantity,
          buying_price: l.buying_price ?? null,
          batch_number: l.batch_number || '',
          expiry_date: l.expiry_date || null,
        }))
    };
    if (!payload.lines.length) {
      error.value = 'No valid lines to apply.';
      return;
    }
    const { data } = await client.post('/api/pharmacy/inventory-transactions/apply_invoice/', payload);
    result.value = data;
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Failed to apply invoice.';
  } finally {
    applying.value = false;
  }
}
</script>

<style scoped>
.card { padding: 12px; border: 1px solid #eee; border-radius: 8px; }
.btn { background: #3b82f6; color: #fff; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; }
.btn.small { padding: 3px 6px; font-size: .85em; }
.pill { background:#eef; color:#224; padding: 2px 6px; border-radius: 12px; font-size:.85em; }
.error { color: #b00020; margin-top: 6px; }
.success { color: #065f46; }
.table-wrap { overflow-x:auto; }
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { border: 1px solid #eee; padding: 6px; font-size: .92em; }
.dropdown { position: relative; background: #fff; border: 1px solid #ddd; border-radius: 6px; margin-top: 4px; max-height: 160px; overflow: auto; }
.dropdown-item { padding: 6px; cursor: pointer; }
.dropdown-item:hover { background: #f6fafe; }
</style>