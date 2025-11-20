<template>
  <div class="card">
    <div class="header">
      <div>
        <h3>Expenses</h3>
        <p class="subtitle">Record operational and stock-related expenses.</p>
      </div>
      <div class="totals" v-if="summary">
        <div class="total-item">
          <span class="label">This Month</span>
          <span class="value">Kshs {{ formatMoney(summary.thisMonth) }}</span>
        </div>
        <div class="total-item">
          <span class="label">Last 30 Days</span>
          <span class="value">Kshs {{ formatMoney(summary.last30) }}</span>
        </div>
      </div>
    </div>

    <form class="form-grid" @submit.prevent="save">
      <div>
        <label>Date *</label>
        <input type="date" v-model="form.occurred_on" required />
      </div>
      <div>
        <label>Category *</label>
        <select v-model="form.category" required>
          <option value="STOCK">Inventory / Stock</option>
          <option value="OPERATIONS">Operations</option>
          <option value="SALARIES">Salaries</option>
          <option value="OTHER">Other</option>
        </select>
      </div>
      <div>
        <label>Vendor / Payee</label>
        <input v-model="form.vendor" placeholder="e.g. ABC Suppliers Ltd" />
      </div>
      <div>
        <label>Reference</label>
        <input v-model="form.reference" placeholder="e.g. INV-1234 / Receipt #" />
      </div>
      <div class="full-width">
        <label>Description *</label>
        <input
          v-model="form.description"
          required
          placeholder="e.g. Purchase of gloves and syringes"
        />
      </div>
      <div>
        <label>Amount (Kshs) *</label>
        <input
          v-model.number="form.amount"
          type="number"
          min="0"
          step="0.01"
          required
        />
      </div>
      <div class="actions">
        <button type="submit" class="btn" :disabled="saving">
          {{ saving ? 'Saving…' : 'Record Expense' }}
        </button>
        <span v-if="saving" class="saving-text">Posting expense…</span>
      </div>
    </form>

    <div v-if="error" class="error-box">
      {{ error }}
    </div>
    <div v-else-if="success" class="success-box">
      {{ success }}
    </div>

    <div class="recent-card">
      <div class="recent-header">
        <h4>Recent Expenses</h4>
        <div class="filters">
          <select v-model="filters.category" @change="loadExpenses">
            <option value="">All Categories</option>
            <option value="STOCK">Inventory / Stock</option>
            <option value="OPERATIONS">Operations</option>
            <option value="SALARIES">Salaries</option>
            <option value="OTHER">Other</option>
          </select>
          <select v-model="filters.range" @change="loadExpenses">
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
      </div>

      <div v-if="loading" class="loading">Loading expenses…</div>
      <div v-else-if="expenses.length === 0" class="empty">No expenses recorded for this period.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Category</th>
            <th>Description</th>
            <th>Vendor</th>
            <th>Reference</th>
            <th class="amount-col">Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exp in expenses" :key="exp.id">
            <td>{{ formatDate(exp.occurred_on) }}</td>
            <td>{{ formatCategory(exp.category) }}</td>
            <td>{{ exp.description || '-' }}</td>
            <td>{{ exp.vendor || '-' }}</td>
            <td>{{ exp.reference || '-' }}</td>
            <td class="amount-col">Kshs {{ formatMoney(exp.amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import api from '@/api/client';

const todayISO = new Date().toISOString().slice(0, 10);

const form = reactive({
  occurred_on: todayISO,
  category: 'STOCK',
  vendor: '',
  description: '',
  amount: 0,
  reference: '',
});

const filters = reactive({
  category: '',
  range: '7',
});

const expenses = ref([]);
const saving = ref(false);
const loading = ref(false);
const error = ref('');
const success = ref('');
const summary = ref(null);

function formatMoney(val) {
  const num = Number(val || 0);
  return num.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(s) {
  try {
    const d = new Date(s);
    return d.toLocaleDateString();
  } catch {
    return s;
  }
}

function formatCategory(code) {
  const map = {
    STOCK: 'Inventory / Stock',
    OPERATIONS: 'Operations',
    SALARIES: 'Salaries',
    OTHER: 'Other',
  };
  return map[code] || code || '-';
}

async function save() {
  error.value = '';
  if (!form.description?.trim()) {
    error.value = 'Please provide a description for the expense.';
    return;
  }
  if (!form.amount || Number(form.amount) <= 0) {
    error.value = 'Amount must be greater than zero.';
    return;
  }

  saving.value = true;
  success.value = '';
  try {
    const payload = {
      occurred_on: form.occurred_on,
      category: form.category,
      vendor: form.vendor?.trim() || '',
      description: form.description?.trim(),
      amount: Number(form.amount),
      reference: form.reference?.trim() || '',
    };
    await api.post('/api/expenses/', payload);
    success.value = 'Expense recorded successfully.';
    setTimeout(() => { success.value = ''; }, 3500);

    // Reset fields for next entry
    form.description = '';
    form.vendor = '';
    form.amount = 0;
    form.reference = '';
    form.category = 'STOCK';
    form.occurred_on = todayISO;

    await loadExpenses();
  } catch (e) {
    if (e.response?.data) {
      error.value = humanizeError(e.response.data);
    } else {
      error.value = e.message || 'Failed to record expense.';
    }
  } finally {
    saving.value = false;
  }
}

function humanizeError(data) {
  if (typeof data === 'string') return data;
  if (Array.isArray(data)) return data.join('; ');
  return Object.entries(data)
    .map(([key, value]) => {
      if (Array.isArray(value)) return `${key}: ${value.join(', ')}`;
      if (typeof value === 'object' && value !== null) return `${key}: ${JSON.stringify(value)}`;
      return `${key}: ${value}`;
    })
    .join(' | ');
}

function computeSummary(list) {
  const now = new Date();
  const msInDay = 24 * 60 * 60 * 1000;
  let thisMonthTotal = 0;
  let last30Total = 0;

  for (const exp of list) {
    const d = new Date(exp.occurred_on);
    if (Number.isNaN(d.getTime())) continue;
    const diffDays = Math.floor((now - d) / msInDay);
    if (diffDays <= 30) {
      last30Total += Number(exp.amount || 0);
    }
    const isSameMonth =
      d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
    if (isSameMonth) {
      thisMonthTotal += Number(exp.amount || 0);
    }
  }

  summary.value = {
    thisMonth: thisMonthTotal,
    last30: last30Total,
  };
}

async function loadExpenses() {
  loading.value = true;
  error.value = '';
  try {
    const days = Number(filters.range || '7');
    const end = new Date();
    const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);
    const startISO = start.toISOString().slice(0, 10);
    const endISO = end.toISOString().slice(0, 10);

    const params = {
      start_date: startISO,
      end_date: endISO,
    };
    if (filters.category) params.category = filters.category;

    const { data } = await api.get('/api/expenses/', { params });
    expenses.value = data || [];
    computeSummary(expenses.value);
  } catch (e) {
    console.error('Failed to load expenses', e);
    error.value = 'Failed to load expenses.';
    success.value = '';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadExpenses();
});
</script>

<style scoped>
.card {
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 15px;
  background: #fff;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.subtitle {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 0.9em;
}

.totals {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.total-item {
  padding: 6px 10px;
  border-radius: 6px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.total-item .label {
  display: block;
  font-size: 0.8em;
  color: #6b7280;
}

.total-item .value {
  font-weight: 600;
  font-size: 0.95em;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px 12px;
  margin-bottom: 10px;
}

label {
  display: block;
  margin-bottom: 4px;
  font-size: 0.85em;
  font-weight: 500;
  color: #374151;
}

input,
select {
  width: 100%;
  padding: 7px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.9em;
}

.full-width {
  grid-column: 1 / -1;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn {
  background: #10b981;
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.saving-text {
  font-size: 0.85em;
  color: #6b7280;
}

.error-box {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  font-size: 0.88em;
}
.success-box {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #047857;
  font-size: 0.88em;
}

.recent-card {
  margin-top: 16px;
}

.recent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.filters {
  display: flex;
  gap: 8px;
}

.loading,
.empty {
  padding: 10px;
  color: #6b7280;
  font-size: 0.9em;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 4px;
  font-size: 0.9em;
}

.table th,
.table td {
  padding: 8px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}

.table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.amount-col {
  text-align: right;
  white-space: nowrap;
}
</style>


