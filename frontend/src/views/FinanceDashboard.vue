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
    // Fetch a couple of metrics to narrate
    const [lowStockRes, profitRes] = await Promise.all([
      client.get('/api/pharmacy/medicines/low_stock/'),
      client.get('/api/pharmacy/inventory-transactions/profit_summary/')
    ]);
    const lowCount = Array.isArray(lowStockRes.data) ? lowStockRes.data.length : 0;
    const profit = profitRes?.data?.profit ?? '0.00';
    const text = `Finance insights: Gross profit is ${profit}. There are ${lowCount} medicine items at or below reorder levels.`;

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