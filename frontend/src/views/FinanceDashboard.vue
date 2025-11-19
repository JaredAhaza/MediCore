<template>
  <div>
    <div class="card">
      <h2>Finance</h2>
      <div style="display:flex; align-items:center; justify-content:space-between;">
        <div style="color:#666; font-size:.95em;">Overview of invoices, payments, and stock spending.</div>
        <button class="btn" @click="voiceInsights" :disabled="speaking">{{ speaking ? 'Speaking…' : 'Voice Insights' }}</button>
      </div>
    </div>
    <FinanceSummary />
    <InvoiceImport />
  </div>
</template>

<script setup>
import FinanceSummary from '@/components/FinanceSummary.vue';
import InvoiceImport from '@/components/InvoiceImport.vue';

import client from '@/api/client';
import { ref } from 'vue';

const speaking = ref(false);

async function voiceInsights() {
  const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY;
  const voiceId = import.meta.env.VITE_ELEVENLABS_VOICE_ID || '21m00Tcm4TlvDq8ikWAM'; // default voice if set
  if (!apiKey) {
    alert('ElevenLabs API key not configured. Set VITE_ELEVENLABS_API_KEY in .env.');
    return;
  }
  speaking.value = true;
  try {
    const [lowStockRes, profitRes, reportRes, invoicesRes] = await Promise.all([
      client.get('/api/pharmacy/medicines/low_stock/'),
      client.get('/api/pharmacy/inventory-transactions/profit_summary/'),
      client.get('/api/finance/reports/financial-position/'),
      client.get('/api/invoices/')
    ]);
    const lowCount = Array.isArray(lowStockRes.data) ? lowStockRes.data.length : 0;
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
      topExpense ? `Largest expense category is ${topExpense.category} at ${formatMoney(topExpense.total)}.` : '',
      `There are ${lowCount} medicines at or below reorder levels, consider restocking soon.`
    ].filter(Boolean);

    const text = narrativeParts.join(' ');

    // Call ElevenLabs TTS
    const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`;
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'xi-api-key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text,
        voice_settings: { stability: 0.5, similarity_boost: 0.5 }
      })
    });
    if (!resp.ok) throw new Error('TTS request failed');
    const blob = await resp.blob();
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.play();
  } catch (e) {
    alert('Failed to generate voice insights.');
  } finally {
    speaking.value = false;
  }
}
</script>

<style scoped>
.card { padding: 12px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 12px; }
.btn { background: #3b82f6; color: #fff; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; }
</style>