<template>
  <div class="card">
    <div style="display:flex; align-items:center; justify-content:space-between;">
      <h3>Finance Overview</h3>
      <RouterLink v-if="auth.access && canViewFinance && !isOnFinancePage" class="btn secondary" :to="{ name: 'FinanceDashboard' }">Open Finance</RouterLink>
    </div>
    <div v-if="!auth.access" style="color:#666; font-size:.95em;">
      Login to view finance status.
    </div>
    <div v-else>
      <div v-if="loading" style="color:#666;">Loading finance data…</div>
      <div v-else-if="error" style="color:#b00020;">{{ error }}</div>
      <div v-else style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
        <div class="stat">
          <div class="label">Pending Invoices</div>
          <div class="value">{{ pendingInvoices }}</div>
        </div>
        <div class="stat clickable" role="button" tabindex="0" @click="showPaidDetails" @keydown.enter="showPaidDetails">
          <div class="label">Money Paid</div>
          <div class="value">{{ formatMoney(moneyPaid) }}</div>
        </div>
        <div class="stat clickable" role="button" tabindex="0" @click="showSpentDetails" @keydown.enter="showSpentDetails">
          <div class="label">Money Spent (Stock In)</div>
          <div class="value">{{ formatMoney(moneySpent) }}</div>
        </div>
        <div class="stat">
          <div class="label">Gross Profit</div>
          <div class="value">{{ formatMoney(grossProfit) }}</div>
        </div>
      </div>
      <div v-if="activeDetail" class="card" style="margin-top:12px;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">
          <div style="display:flex; gap:8px; align-items:center;">
            <h3 v-if="activeDetail==='paid'" style="margin:0;">Money Paid — Payments</h3>
            <h3 v-else style="margin:0;">Money Spent — Stock In</h3>
          </div>
          <div style="display:flex; gap:8px; align-items:center;">
            <button class="btn secondary" @click="exportCSV">Export CSV</button>
            <button class="btn secondary" @click="exportPDF">Export PDF</button>
            <button class="btn" @click="printDetails">Print</button>
            <button class="btn danger" @click="closeDetails">Close</button>
          </div>
        </div>

        <div v-if="activeDetail==='paid'">
          <div v-if="!paymentsList.length" style="color:#666;">No payments recorded.</div>
          <table v-else class="table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Reference</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in paymentsList" :key="p.id">
                <td>#{{ p.invoice }}</td>
                <td>{{ formatMoney(p.amount) }}</td>
                <td>{{ p.method }}</td>
                <td>{{ p.reference || '-' }}</td>
                <td>{{ formatDate(p.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else>
          <div v-if="!stockInList.length" style="color:#666;">No stock-in records.</div>
          <table v-else class="table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Quantity</th>
                <th>Buying Price</th>
                <th>Total Cost</th>
                <th>Batch</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in stockInList" :key="t.id">
                <td>{{ t.medicine_name }}</td>
                <td>{{ t.quantity }}</td>
                <td>{{ formatMoney(buyingPriceMap.get(t.medicine) || 0) }}</td>
                <td>{{ formatMoney((buyingPriceMap.get(t.medicine) || 0) * (Number(t.quantity) || 0)) }}</td>
                <td>{{ t.batch_number || '-' }}</td>
                <td>{{ formatDate(t.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import api from '@/api/client';
import { useAuthStore } from '@/stores/auth';

  const auth = useAuthStore();
  const route = useRoute();
const loading = ref(false);
const error = ref("");
const pendingInvoices = ref(0);
const moneyPaid = ref(0);
const moneySpent = ref(0);
const grossProfit = ref(0);
const paymentsList = ref([]);
const stockInList = ref([]);
const activeDetail = ref(null); // 'paid' | 'spent' | null
const buyingPriceMap = new Map();

  const canViewFinance = computed(() => ['ADMIN','FINANCE'].includes(auth.user?.role));
  const isOnFinancePage = computed(() => route.name === 'FinanceDashboard');

  function formatMoney(n) {
    const num = Number(n || 0);
    return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function formatDate(s) {
    try {
      const d = new Date(s);
      return d.toLocaleString();
    } catch { return s; }
  }
  function showPaidDetails() { activeDetail.value = 'paid'; }
  function showSpentDetails() { activeDetail.value = 'spent'; }
  function closeDetails() { activeDetail.value = null; }

  function csvEscape(val) {
    const s = String(val ?? '');
    if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  }

  function exportCSV() {
    const isPaid = activeDetail.value === 'paid';
    let rows = [];
    let header = [];
    if (isPaid) {
      header = ['Invoice','Amount','Method','Reference','Date'];
      rows = paymentsList.value.map(p => [p.invoice, p.amount, p.method, p.reference || '', formatDate(p.created_at)]);
    } else {
      header = ['Medicine','Quantity','Buying Price','Total Cost','Batch','Date'];
      rows = stockInList.value.map(t => {
        const buy = buyingPriceMap.get(t.medicine) || 0;
        return [t.medicine_name, t.quantity, buy, (buy * (Number(t.quantity)||0)), t.batch_number || '', formatDate(t.created_at)];
      });
    }
    const csv = [header.map(csvEscape).join(','), ...rows.map(r => r.map(csvEscape).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
    a.download = isPaid ? `payments_${ts}.csv` : `stock_in_${ts}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function buildPrintableHTML() {
    const isPaid = activeDetail.value === 'paid';
    const title = isPaid ? 'Money Paid — Payments' : 'Money Spent — Stock In';
    const styles = `
      <style>
        body { font-family: Arial, sans-serif; padding: 16px; }
        h2 { margin: 0 0 12px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f3f4f6; }
      </style>
    `;
    let table = '';
    if (isPaid) {
      table = `
        <table>
          <thead>
            <tr><th>Invoice</th><th>Amount</th><th>Method</th><th>Reference</th><th>Date</th></tr>
          </thead>
          <tbody>
            ${paymentsList.value.map(p => `<tr>
              <td>#${p.invoice}</td>
              <td>${formatMoney(p.amount)}</td>
              <td>${p.method}</td>
              <td>${p.reference || '-'}</td>
              <td>${formatDate(p.created_at)}</td>
            </tr>`).join('')}
          </tbody>
        </table>`;
    } else {
      table = `
        <table>
          <thead>
            <tr><th>Medicine</th><th>Quantity</th><th>Buying Price</th><th>Total Cost</th><th>Batch</th><th>Date</th></tr>
          </thead>
          <tbody>
            ${stockInList.value.map(t => {
              const buy = buyingPriceMap.get(t.medicine) || 0;
              const total = buy * (Number(t.quantity)||0);
              return `<tr>
                <td>${t.medicine_name}</td>
                <td>${t.quantity}</td>
                <td>${formatMoney(buy)}</td>
                <td>${formatMoney(total)}</td>
                <td>${t.batch_number || '-'}</td>
                <td>${formatDate(t.created_at)}</td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>`;
    }
    return `<!doctype html><html><head>${styles}</head><body><h2>${title}</h2>${table}</body></html>`;
  }

  function exportPDF() {
    // Use browser print-to-PDF to export; opens a printable view
    const html = buildPrintableHTML();
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.open();
    w.document.write(html);
    w.document.close();
    w.focus();
    // Delay print slightly to ensure rendering
    setTimeout(() => { try { w.print(); } catch {} }, 250);
  }

  function printDetails() {
    const html = buildPrintableHTML();
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.open();
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => { try { w.print(); } catch {} }, 250);
  }

async function loadFinance() {
  if (!auth.access) return; // don't load if not logged in
  loading.value = true;
  error.value = "";
  try {
    const [invRes, payRes] = await Promise.all([
      api.get('/api/invoices/'),
      api.get('/api/payments/')
    ]);
    const invoices = invRes.data || [];
    const payments = payRes.data || [];
    paymentsList.value = payments;

    pendingInvoices.value = invoices.filter(i => i.status === 'DUE').length;
    moneyPaid.value = payments.reduce((sum, p) => sum + Number(p.amount || 0), 0);

    // Compute money spent from stock-in transactions (quantity * buying_price)
    const [transRes, medsRes] = await Promise.all([
      api.get('/api/pharmacy/inventory-transactions/', { params: { transaction_type: 'STOCK_IN' } }),
      api.get('/api/pharmacy/medicines', { params: { is_active: true } })
    ]);
    const transactions = transRes.data || [];
    const meds = medsRes.data || [];
    stockInList.value = transactions;
    for (const m of meds) buyingPriceMap.set(m.id, Number(m.buying_price || 0));
    moneySpent.value = transactions.reduce((sum, t) => {
      const price = buyingPriceMap.get(t.medicine) || 0;
      const qty = Number(t.quantity || 0);
      return sum + price * qty;
    }, 0);

    // Gross profit from dispensed transactions
    const profitRes = await api.get('/api/pharmacy/inventory-transactions/profit_summary/');
    const ps = profitRes.data || {};
    grossProfit.value = Number(ps.profit || 0);
  } catch (e) {
    error.value = 'Failed to load finance data';
  } finally {
    loading.value = false;
  }
}

onMounted(loadFinance);
</script>

<style scoped>
.stat {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
}
.stat .label { color: #6b7280; font-size: .9em; }
.stat .value { font-size: 1.4em; font-weight: 600; margin-top: 4px; }
</style>