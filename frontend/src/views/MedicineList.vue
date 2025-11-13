<template>
  <div>
    <div class="card">
      <h3>Medicine Inventory</h3>
      <div style="display: flex; gap: 10px; margin-top: 10px;">
        <input v-model="search" placeholder="Search medicines..." @input="debouncedLoad" style="flex: 1;" />
        <select v-model="category" style="padding: 8px;">
          <option value="">All Categories</option>
          <option value="TABLET">Tablet</option>
          <option value="CAPSULE">Capsule</option>
          <option value="SYRUP">Syrup</option>
          <option value="INJECTION">Injection</option>
          <option value="CREAM">Cream/Ointment</option>
          <option value="DROPS">Drops</option>
          <option value="INHALER">Inhaler</option>
          <option value="OTHER">Other</option>
        </select>
        <button class="btn" @click="onPrimary" :disabled="loading">{{ primaryLabel }}</button>
        <button v-if="category" class="btn btn-secondary" @click="clearFilters" :disabled="loading">Clear</button>
      </div>
      <p v-if="error" style="color:#d63031; margin-top:8px;">{{ error }}</p>
    </div>

    <div v-if="loading" class="card" style="text-align:center;">Loading...</div>

    <div v-for="medicine in medicines" :key="medicine.id" class="card" v-show="!loading">
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
          <h4 style="margin: 0;">{{ medicine.name }}</h4>
          <div style="color: #666; font-size: 0.9em; margin: 5px 0;">
            {{ medicine.generic_name || 'No generic name' }} • {{ medicine.category }}
          </div>
          <div v-if="medicine.manufacturer" style="color: #999; font-size: 0.85em;">
            Manufacturer: {{ medicine.manufacturer }}
          </div>
          <div style="margin-top: 10px;">
            <span style="padding: 5px 10px; background: #f1f3f5; border-radius: 4px; font-size: 0.9em; margin-right: 10px;">
              Stock: <b>{{ medicine.current_stock }}</b>
            </span>
            <span style="padding: 5px 10px; background: #f1f3f5; border-radius: 4px; font-size: 0.9em; margin-right: 10px;">
              Reorder: {{ medicine.reorder_level }}
            </span>
            <span style="padding: 5px 10px; background: #f1f3f5; border-radius: 4px; font-size: 0.9em; margin-right:10px;">
              Buying: Kshs {{ medicine.buying_price }}
            </span>
            <span style="padding: 5px 10px; background: #f1f3f5; border-radius: 4px; font-size: 0.9em;">
              Selling: Kshs {{ medicine.selling_price }}
            </span>
          </div>
        </div>
        <div style="text-align: right;">
          <span :style="getStockBadgeStyle(medicine.stock_status)">
            {{ medicine.stock_status.replace('_', ' ') }}
          </span>
          <div style="margin-top: 10px;">
            <router-link :to="`/pharmacy/medicines/${medicine.id}/details`" class="link-btn">View Details</router-link>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && medicines.length === 0" class="card" style="text-align: center; color: #999;">
      No medicines found
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/client';

const router = useRouter();

const search = ref('');
const category = ref('');
const medicines = ref([]);
const loading = ref(false);
const error = ref('');
let timer;

async function load({ forceCategoryOnly = false } = {}) {
  loading.value = true;
  error.value = '';
  try {
    const params = {};
    if (!forceCategoryOnly && search.value) params.search = search.value;
    if (category.value) params.category = category.value;
    const { data } = await api.get('/api/pharmacy/medicines/', { params });
    medicines.value = data;
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load medicines';
  } finally {
    loading.value = false;
  }
}

function debouncedLoad() {
  clearTimeout(timer);
  timer = setTimeout(() => load(), 300);
}

const primaryLabel = computed(() => (category.value ? 'Search' : 'Add Medicine'));

async function onPrimary() {
  if (category.value) {
    await load({ forceCategoryOnly: true }); // strict category-only filter
  } else {
    router.push('/pharmacy/medicines/new');
  }
}

function clearFilters() {
  category.value = '';
  search.value = '';
  load();
}

function getStockBadgeStyle(status) {
  const styles = {
    OUT_OF_STOCK: 'padding: 8px 12px; background: #d63031; color: white; border-radius: 4px; font-weight: bold; display: inline-block;',
    LOW_STOCK: 'padding: 8px 12px; background: #fdcb6e; color: #333; border-radius: 4px; font-weight: bold; display: inline-block;',
    IN_STOCK: 'padding: 8px 12px; background: #00b894; color: white; border-radius: 4px; font-weight: bold; display: inline-block;'
  };
  return styles[status] || '';
}

// initial load
load();
</script>

<style scoped>
.btn {
  padding: 10px 20px;
  background: #0984e3;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  display: inline-block;
  border: none;
  cursor: pointer;
}
.btn:hover {
  background: #0652a3;
}
.btn-secondary {
  background: #636e72;
  color: white;
}
.link-btn {
  padding: 6px 12px;
  background: #0984e3;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.9em;
}
.link-btn:hover {
  background: #0652a3;
}
</style>