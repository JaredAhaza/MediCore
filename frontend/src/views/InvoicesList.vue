<template>
  <div>
    <div class="card">
      <h2>Invoices</h2>
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div style="color: #666; font-size: 0.95em;">
          View and download all invoices
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button class="btn" @click="downloadAll" :disabled="loading">
            {{ loading ? 'Downloading...' : 'Download All (CSV)' }}
          </button>
          <button class="btn secondary" @click="loadInvoices" :disabled="loading">
            Refresh
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>Filters</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
        <div>
          <label>Start Date</label>
          <input type="date" v-model="filters.start_date" @change="loadInvoices" />
        </div>
        <div>
          <label>End Date</label>
          <input type="date" v-model="filters.end_date" @change="loadInvoices" />
        </div>
        <div>
          <label>Status</label>
          <select v-model="filters.status" @change="loadInvoices">
            <option value="">All</option>
            <option value="DUE">Due</option>
            <option value="PAID">Paid</option>
            <option value="VOID">Void</option>
          </select>
        </div>
        <div>
          <label>Search</label>
          <input type="text" v-model="filters.search" placeholder="Patient name or ID" @input="debouncedLoad" />
        </div>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" style="text-align: center; padding: 20px; color: #666;">
        Loading invoices...
      </div>
      <div v-else-if="error" style="color: #d63031; padding: 10px; background: #fee; border-radius: 4px;">
        {{ error }}
      </div>
      <div v-else-if="invoices.length === 0" style="text-align: center; padding: 20px; color: #666;">
        No invoices found
      </div>
      <div v-else>
        <div style="margin-bottom: 10px; color: #666;">
          Showing {{ invoices.length }} invoice(s)
        </div>
        <table class="table">
          <thead>
            <tr>
              <th>Invoice ID</th>
              <th>Patient</th>
              <th>Medical ID</th>
              <th>Status</th>
              <th>Subtotal</th>
              <th>Discount</th>
              <th>Total</th>
              <th>Created At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="invoice in invoices" :key="invoice.id">
              <td>#{{ invoice.id }}</td>
              <td>{{ invoice.patient_detail?.name || 'N/A' }}</td>
              <td>{{ invoice.patient_detail?.medical_id || 'N/A' }}</td>
              <td>
                <span :style="getStatusBadge(invoice.status)">{{ invoice.status }}</span>
              </td>
              <td>Kshs {{ formatMoney(invoice.subtotal) }}</td>
              <td>Kshs {{ formatMoney(invoice.discount) }}</td>
              <td><strong>Kshs {{ formatMoney(invoice.total) }}</strong></td>
              <td>{{ formatDate(invoice.created_at) }}</td>
              <td>
                <button 
                  class="btn-small" 
                  @click="downloadInvoice(invoice.id)"
                  :disabled="downloading === invoice.id"
                >
                  {{ downloading === invoice.id ? '...' : 'Download' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api/client';

const invoices = ref([]);
const loading = ref(false);
const error = ref('');
const downloading = ref(null);
let debounceTimer = null;

const filters = ref({
  start_date: '',
  end_date: '',
  status: '',
  search: ''
});

function formatMoney(val) {
  const num = Number(val || 0);
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleString();
  } catch {
    return dateStr;
  }
}

function getStatusBadge(status) {
  const styles = {
    DUE: 'padding: 4px 8px; background: #ff7675; color: white; border-radius: 4px; font-size: 0.85em;',
    PAID: 'padding: 4px 8px; background: #00b894; color: white; border-radius: 4px; font-size: 0.85em;',
    VOID: 'padding: 4px 8px; background: #b2bec3; color: #2d3436; border-radius: 4px; font-size: 0.85em;'
  };
  return styles[status] || '';
}

function debouncedLoad() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadInvoices, 300);
}

async function loadInvoices() {
  loading.value = true;
  error.value = '';
  try {
    const params = {};
    if (filters.value.start_date) params.start_date = filters.value.start_date;
    if (filters.value.end_date) params.end_date = filters.value.end_date;
    if (filters.value.status) params.status = filters.value.status;
    if (filters.value.search) params.search = filters.value.search;
    
    const { data } = await api.get('/api/invoices/', { params });
    invoices.value = data || [];
  } catch (err) {
    console.error('Failed to load invoices:', err);
    error.value = 'Failed to load invoices. Please try again.';
  } finally {
    loading.value = false;
  }
}

async function downloadInvoice(invoiceId) {
  downloading.value = invoiceId;
  try {
    const response = await api.get(`/api/invoices/${invoiceId}/download/`, {
      responseType: 'blob'
    });
    
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `invoice_${invoiceId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Failed to download invoice:', err);
    alert('Failed to download invoice. Please try again.');
  } finally {
    downloading.value = null;
  }
}

async function downloadAll() {
  loading.value = true;
  try {
    const params = {};
    if (filters.value.start_date) params.start_date = filters.value.start_date;
    if (filters.value.end_date) params.end_date = filters.value.end_date;
    if (filters.value.status) params.status = filters.value.status;
    
    const response = await api.get('/api/invoices/download-all/', {
      params,
      responseType: 'blob'
    });
    
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const today = new Date().toISOString().split('T')[0];
    link.download = `invoices_${today}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Failed to download invoices:', err);
    alert('Failed to download invoices. Please try again.');
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadInvoices();
});
</script>

<style scoped>
.card {
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 15px;
  background: white;
}

.btn {
  background: #0984e3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
}

.btn:hover {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.secondary {
  background: #636e72;
}

.btn-small {
  background: #0984e3;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
}

.btn-small:hover {
  opacity: 0.9;
}

.btn-small:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  font-size: 0.9em;
  color: #555;
}

input[type="date"],
input[type="text"],
select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.table th,
.table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
}

.table tr:hover {
  background: #f8f9fa;
}
</style>

