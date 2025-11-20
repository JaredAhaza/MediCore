<template>
  <div>
    <div class="card">
      <h2>Finance</h2>
      <div style="display:flex; align-items:center; justify-content:space-between;">
        <div style="color:#666; font-size:.95em;">Overview of invoices, payments, and stock spending.</div>
        <div style="display:flex; gap:10px;">
          <RouterLink to="/finance/invoices" class="btn secondary">View All Invoices</RouterLink>
          <button class="btn" @click="voiceInsights" :disabled="speaking">{{ speaking ? 'Speaking…' : 'Voice Insights' }}</button>
        </div>
      </div>
    </div>
    <FinanceSummary />
    <ExpensesPanel />
    <InvoiceImport />
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router';
import FinanceSummary from '@/components/FinanceSummary.vue';
import InvoiceImport from '@/components/InvoiceImport.vue';
import ExpensesPanel from '@/components/ExpensesPanel.vue';

import client from '@/api/client';
import { useVoiceInsights } from '@/composables/useVoiceInsights';

const { speaking, speakInsights } = useVoiceInsights();

async function voiceInsights() {
  try {
    const [profitRes, reportRes, invoicesRes] = await Promise.all([
      client.get('/api/pharmacy/inventory-transactions/profit_summary/'),
      client.get('/api/finance/reports/financial-position/'),
      client.get('/api/invoices/')
    ]);
    const profit = Number(profitRes?.data?.profit ?? 0).toFixed(2);
    const report = reportRes?.data || {};
    const totals = report.totals || {};
    const breakdown = report.breakdown || {};
    const period = report.period || {};
    const pendingInvoices = (invoicesRes?.data || []).filter(inv => inv.status === 'DUE').length;

    const formatMoney = (val) => Number(val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const topRevenue = breakdown.revenue_by_category?.[0];
    const topExpense = breakdown.expenses_by_category?.[0];

    const narrativeParts = [
      `Finance insights for the period ${period.start_date || 'start of month'} to ${period.end_date || 'today'}.`,
      `Net position stands at ${formatMoney(totals.net_position)} shillings with revenue ${formatMoney(totals.revenue)} and expenses ${formatMoney(totals.expenses)}.`,
      `Cash collected is ${formatMoney(totals.cash_collected)} and accounts receivable are ${formatMoney(totals.accounts_receivable)} with ${pendingInvoices} invoices still pending payment.`,
      `Gross profit from dispensing activity is ${formatMoney(profit)}.`,
      topRevenue ? `Top revenue source is ${topRevenue.category} contributing ${formatMoney(topRevenue.total)}.` : '',
      topExpense ? `Largest expense category is ${topExpense.category} at ${formatMoney(topExpense.total)}.` : ''
    ].filter(Boolean);

    await speakInsights(narrativeParts);
  } catch (e) {
    alert('Failed to generate voice insights.');
  }
}
</script>

<style scoped>
.card { padding: 12px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 12px; }
.btn { background: #3b82f6; color: #fff; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; }
.btn.secondary { background: #636e72; }
.btn:hover { opacity: 0.9; }
</style>