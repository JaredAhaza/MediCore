<template>
    <div>
      <div class="card" v-if="medicine">
        <h3 style="margin-top:0;">{{ medicine.name }}</h3>
        <div style="color:#666; margin-bottom:10px;">
          {{ medicine.generic_name || 'No generic name' }} • {{ medicine.category }}
        </div>
  
        <div class="grid">
          <div><b>Manufacturer:</b> {{ medicine.manufacturer || '—' }}</div>
          <div><b>Unit Price:</b> ${{ medicine.unit_price }}</div>
          <div><b>Current Stock:</b> {{ medicine.current_stock }}</div>
          <div><b>Reorder Level:</b> {{ medicine.reorder_level }}</div>
          <div><b>Status:</b> {{ medicine.stock_status.replace('_', ' ') }}</div>
          <div><b>Active:</b> {{ medicine.is_active ? 'Yes' : 'No' }}</div>
        </div>
  
        <div style="margin-top:10px;">
          <b>Description:</b>
          <div style="white-space:pre-wrap; color:#444; margin-top:6px;">
            {{ medicine.description || '—' }}
          </div>
        </div>
  
        <div style="margin-top:16px; display:flex; gap:10px;">
          <router-link :to="`/pharmacy/medicines/${medicine.id}`" class="btn">Edit</router-link>
          <router-link to="/pharmacy/medicines" class="btn btn-secondary">Back to list</router-link>
        </div>
      </div>
  
      <div class="card" v-else>
        Loading...
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import api from '../api/client';
  
  const route = useRoute();
  const medicine = ref(null);
  
  onMounted(async () => {
    const { data } = await api.get(`/api/pharmacy/medicines/${route.params.id}/`);
    medicine.value = data;
  });
  </script>
  
  <style scoped>
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 16px;
    margin-bottom: 10px;
  }
  .btn {
    padding: 10px 20px;
    background: #0984e3;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    display: inline-block;
  }
  .btn-secondary {
    background: #636e72;
    color: white;
  }
  .btn:hover {
    opacity: 0.9;
  }
  </style>