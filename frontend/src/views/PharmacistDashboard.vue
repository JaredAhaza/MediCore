<template>
  <div class="dashboard">
    <div class="header">
      <h1>Pharmacist Dashboard</h1>
      <p>Pharmacy operations and prescription management</p>
    </div>

    <!-- Quick Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: #e74c3c;">⚠️</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.lowStockItems }}</div>
          <div class="stat-label">Low Stock Alerts</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #3498db;">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pendingPrescriptions }}</div>
          <div class="stat-label">Pending Prescriptions</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #2ecc71;">💊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalMedicines }}</div>
          <div class="stat-label">Total Medicines</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #f39c12;">💰</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pendingInvoices }}</div>
          <div class="stat-label">Pending Invoices</div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="section">
      <h2>Quick Actions</h2>
      <div class="actions-grid">
        <router-link to="/emr/prescriptions/new" class="action-card primary">
          <div class="action-icon">📝</div>
          <div class="action-title">New Prescription</div>
          <div class="action-desc">Create a new prescription</div>
        </router-link>
        <router-link to="/pharmacy/dispense" class="action-card success">
          <div class="action-icon">💊</div>
          <div class="action-title">Dispense Prescription</div>
          <div class="action-desc">Dispense medicine to patients</div>
        </router-link>
        <router-link to="/finance/invoices" class="action-card warning">
          <div class="action-icon">📄</div>
          <div class="action-title">Generate Invoice</div>
          <div class="action-desc">Create billing invoice</div>
        </router-link>
        <router-link to="/finance" class="action-card info">
          <div class="action-icon">💳</div>
          <div class="action-title">Record Payment</div>
          <div class="action-desc">Process patient payments</div>
        </router-link>
      </div>
    </div>

    <!-- Pharmacy Modules -->
    <div class="section">
      <h2>Pharmacy Operations</h2>
      <div class="modules-grid">
        <router-link to="/pharmacy/medicines" class="module-card">
          <div class="module-icon">💊</div>
          <h3>Medicine Inventory</h3>
          <p>View and manage medicine stock</p>
        </router-link>
        <router-link to="/pharmacy/stock" class="module-card">
          <div class="module-icon">📦</div>
          <h3>Stock Management</h3>
          <p>Add stock and track inventory</p>
        </router-link>
        <router-link to="/emr/prescriptions" class="module-card">
          <div class="module-icon">📋</div>
          <h3>Prescriptions</h3>
          <p>View all prescriptions</p>
        </router-link>
        <router-link to="/pharmacy/dispense" class="module-card">
          <div class="module-icon">🎯</div>
          <h3>Dispense Queue</h3>
          <p>Pending prescriptions to dispense</p>
        </router-link>
      </div>
    </div>

    <!-- Low Stock Alerts -->
    <div v-if="lowStockItems.length > 0" class="section">
      <div class="alert-header">
        <h2>⚠️ Low Stock Alerts</h2>
        <router-link to="/pharmacy/medicines" class="btn-link">View All</router-link>
      </div>
      <div class="alerts-list">
        <div v-for="item in lowStockItems.slice(0, 5)" :key="item.id" class="alert-item">
          <div class="alert-info">
            <div class="alert-name">{{ item.name }}</div>
            <div class="alert-details">
              Current: <strong :class="item.current_stock === 0 ? 'text-danger' : 'text-warning'">
                {{ item.current_stock }}
              </strong> | 
              Reorder Level: {{ item.reorder_level }}
            </div>
          </div>
          <router-link :to="`/pharmacy/medicines/${item.id}`" class="btn-small">Restock</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api/client';

const stats = ref({
  lowStockItems: 0,
  pendingPrescriptions: 0,
  totalMedicines: 0,
  pendingInvoices: 0
});

const lowStockItems = ref([]);

async function loadStats() {
  try {
    const [lowStockRes, prescriptionsRes, medicinesRes, invoicesRes] = await Promise.all([
      api.get('/api/pharmacy/medicines/low_stock/').catch(() => ({ data: [] })),
      api.get('/api/prescriptions/?status=PENDING').catch(() => ({ data: [] })),
      api.get('/api/pharmacy/medicines/').catch(() => ({ data: [] })),
      api.get('/api/invoices/?status=DUE').catch(() => ({ data: [] }))
    ]);

    lowStockItems.value = lowStockRes.data;
    stats.value.lowStockItems = lowStockRes.data.length || 0;
    stats.value.pendingPrescriptions = prescriptionsRes.data.length || 0;
    stats.value.totalMedicines = medicinesRes.data.length || 0;
    stats.value.pendingInvoices = invoicesRes.data.length || 0;
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

onMounted(() => {
  loadStats();
  // Refresh every 30 seconds
  setInterval(loadStats, 30000);
});
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.5em;
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.header p {
  color: #7f8c8d;
  font-size: 1.1em;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8em;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2em;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  color: #7f8c8d;
  font-size: 0.9em;
}

.section {
  margin-bottom: 40px;
}

.section h2 {
  font-size: 1.8em;
  margin-bottom: 20px;
  color: #2c3e50;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.action-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  text-decoration: none;
  color: #2c3e50;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid #3498db;
}

.action-card.primary {
  border-left-color: #3498db;
}

.action-card.success {
  border-left-color: #2ecc71;
}

.action-card.warning {
  border-left-color: #f39c12;
}

.action-card.info {
  border-left-color: #9b59b6;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}

.action-icon {
  font-size: 2.5em;
  margin-bottom: 10px;
}

.action-title {
  font-size: 1.2em;
  font-weight: bold;
  margin-bottom: 8px;
}

.action-desc {
  color: #7f8c8d;
  font-size: 0.9em;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.module-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  text-decoration: none;
  color: #2c3e50;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  border-top: 4px solid #3498db;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}

.module-icon {
  font-size: 2.5em;
  margin-bottom: 15px;
}

.module-card h3 {
  margin: 0 0 10px 0;
  font-size: 1.3em;
}

.module-card p {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.95em;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-link {
  color: #3498db;
  text-decoration: none;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 6px;
  transition: background 0.2s;
}

.btn-link:hover {
  background: #ecf0f1;
}

.alerts-list {
  background: #fff3cd;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #f39c12;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  margin-bottom: 10px;
}

.alert-item:last-child {
  margin-bottom: 0;
}

.alert-info {
  flex: 1;
}

.alert-name {
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 5px;
  color: #2c3e50;
}

.alert-details {
  color: #7f8c8d;
  font-size: 0.9em;
}

.text-danger {
  color: #e74c3c;
}

.text-warning {
  color: #f39c12;
}

.btn-small {
  padding: 8px 16px;
  background: #3498db;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.9em;
  transition: background 0.2s;
}

.btn-small:hover {
  background: #2980b9;
}
</style>
