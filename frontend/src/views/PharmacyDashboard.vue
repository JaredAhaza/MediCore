<template>
  <div>
    <div class="card">
      <div class="card-header">
        <div>
          <h2>Pharmacy Dashboard</h2>
          <p>Inventory management and low stock alerts</p>
        </div>
        <button class="btn" type="button" @click="voiceInsights" :disabled="speaking">
          {{ speaking ? 'Speaking…' : 'Voice Insights' }}
        </button>
      </div>
    </div>

    <div v-if="lowStockCount > 0" class="card" style="background: #fff3cd; border-left: 4px solid #ff6b6b;">
      <h3 style="color: #d63031;">⚠️ Low Stock Alerts ({{ lowStockCount }})</h3>
      <div v-for="item in lowStockItems" :key="item.id" style="margin: 10px 0; padding: 10px; background: white; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <b>{{ item.name }}</b> ({{ item.category }})
            <div style="font-size: 0.9em; color: #666;">
              Current Stock: <b style="color: #d63031;">{{ item.current_stock }}</b> | 
              Reorder Level: {{ item.reorder_level }} | 
              Deficit: {{ item.stock_deficit }}
            </div>
          </div>
          <span :style="getStockStatusStyle(item.stock_status)">{{ item.stock_status }}</span>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>Quick Stats</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
        <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
          <div style="font-size: 2em; font-weight: bold; color: #0984e3;">{{ stats.total_medicines }}</div>
          <div style="color: #666;">Total Medicines</div>
        </div>
        <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
          <div style="font-size: 2em; font-weight: bold; color: #00b894;">{{ stats.in_stock }}</div>
          <div style="color: #666;">In Stock</div>
        </div>
        <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
          <div style="font-size: 2em; font-weight: bold; color: #fdcb6e;">{{ lowStockCount }}</div>
          <div style="color: #666;">Low Stock</div>
        </div>
        <div style="padding: 15px; background: #f8f9fa; border-radius: 8px;">
          <div style="font-size: 2em; font-weight: bold; color: #d63031;">{{ stats.out_of_stock }}</div>
          <div style="color: #666;">Out of Stock</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>Quick Actions</h3>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <router-link to="/pharmacy/medicines" class="btn">View All Medicines</router-link>
        <router-link to="/pharmacy/medicines/new" class="btn">Add New Medicine</router-link>
        <router-link to="/pharmacy/stock" class="btn">Manage Stock</router-link>
        <router-link to="/pharmacy/dispense" class="btn">Dispense Prescription</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../api/client';
import { useVoiceInsights } from '@/composables/useVoiceInsights';

const lowStockItems = ref([]);
const medicines = ref([]);
const stats = ref({
  total_medicines: 0,
  in_stock: 0,
  out_of_stock: 0
});

const lowStockCount = computed(() => lowStockItems.value.length);
const { speaking, speakInsights } = useVoiceInsights();

async function loadDashboard() {
  try {
    const [lowStockRes, medicinesRes] = await Promise.all([
      api.get('/api/pharmacy/medicines/low_stock/'),
      api.get('/api/pharmacy/medicines/')
    ]);
    
    lowStockItems.value = lowStockRes.data;
    medicines.value = medicinesRes.data;
    
    stats.value.total_medicines = medicines.value.length;
    stats.value.in_stock = medicines.value.filter(m => m.stock_status === 'IN_STOCK').length;
    stats.value.out_of_stock = medicines.value.filter(m => m.stock_status === 'OUT_OF_STOCK').length;
  } catch (error) {
    console.error('Failed to load dashboard:', error);
  }
}

function getStockStatusStyle(status) {
  const styles = {
    OUT_OF_STOCK: 'padding: 5px 10px; background: #d63031; color: white; border-radius: 4px; font-size: 0.85em;',
    LOW_STOCK: 'padding: 5px 10px; background: #fdcb6e; color: #333; border-radius: 4px; font-size: 0.85em;',
    IN_STOCK: 'padding: 5px 10px; background: #00b894; color: white; border-radius: 4px; font-size: 0.85em;'
  };
  return styles[status] || '';
}

onMounted(() => {
  loadDashboard();
  setInterval(loadDashboard, 30000); // Refresh every 30 seconds
});

async function voiceInsights() {
  try {
    await loadDashboard();
    const criticalList = lowStockItems.value
      .slice(0, 3)
      .map(item => `${item.name} with only ${item.current_stock} units left`);
    const categories = medicines.value.reduce((acc, med) => {
      if (!med.category) return acc;
      acc[med.category] = (acc[med.category] || 0) + 1;
      return acc;
    }, {});
    const topCategory = Object.entries(categories).sort((a, b) => b[1] - a[1])[0];

    const parts = [
      `Pharmacy inventory overview: ${stats.value.total_medicines} medicines tracked.`,
      `${stats.value.in_stock} items are healthy, ${lowStockCount.value} are running low, and ${stats.value.out_of_stock} are out of stock.`,
      topCategory ? `${topCategory[0]} is the busiest category with ${topCategory[1]} distinct medicines.` : '',
      criticalList.length
        ? `Immediate restock needed for ${criticalList.join(', ')}.`
        : 'No medicines are critically low right now.'
    ];

    await speakInsights(parts);
  } catch (error) {
    console.error('Pharmacy voice insights failed', error);
    alert('Unable to generate pharmacy voice insights.');
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.btn {
  padding: 10px 20px;
  background: #0984e3;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  display: inline-block;
}
.btn:hover {
  background: #0652a3;
}
</style>
