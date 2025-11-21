<template>
  <div class="dashboard">
    <div class="header">
      <h1>Admin Dashboard</h1>
      <p>Complete system overview and user management</p>
    </div>

    <!-- Quick Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: #3498db;">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalUsers }}</div>
          <div class="stat-label">Total Users</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #2ecc71;">🏥</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalPatients }}</div>
          <div class="stat-label">Patients</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #e74c3c;">💊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.lowStockItems }}</div>
          <div class="stat-label">Low Stock Alerts</div>
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
        <router-link to="/admin/users/new" class="action-card">
          <div class="action-icon">👤</div>
          <div class="action-title">Register New User</div>
          <div class="action-desc">Add staff members to the system</div>
        </router-link>
        <router-link to="/patients/new" class="action-card">
          <div class="action-icon">🏥</div>
          <div class="action-title">New Patient</div>
          <div class="action-desc">Register a new patient</div>
        </router-link>
        <router-link to="/pharmacy/medicines/new" class="action-card">
          <div class="action-icon">💊</div>
          <div class="action-title">Add Medicine</div>
          <div class="action-desc">Add new medicine to inventory</div>
        </router-link>
        <router-link to="/finance/invoices" class="action-card">
          <div class="action-icon">📄</div>
          <div class="action-title">View Invoices</div>
          <div class="action-desc">Manage billing and payments</div>
        </router-link>
      </div>
    </div>

    <!-- System Modules -->
    <div class="section">
      <h2>System Modules</h2>
      <div class="modules-grid">
        <router-link to="/admin/users" class="module-card">
          <h3>👥 User Management</h3>
          <p>Manage staff accounts and roles</p>
        </router-link>
        <router-link to="/patients" class="module-card">
          <h3>🏥 Patient Management</h3>
          <p>View and manage patient records</p>
        </router-link>
        <router-link to="/emr/prescriptions" class="module-card">
          <h3>📋 Prescriptions</h3>
          <p>Manage prescriptions and treatments</p>
        </router-link>
        <router-link to="/pharmacy" class="module-card">
          <h3>💊 Pharmacy</h3>
          <p>Inventory and dispensing</p>
        </router-link>
        <router-link to="/finance" class="module-card">
          <h3>💰 Finance</h3>
          <p>Billing, payments, and reports</p>
        </router-link>
        <router-link to="/emr/treatment-notes" class="module-card">
          <h3>📝 Treatment Notes</h3>
          <p>Medical records and notes</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api/client';

const stats = ref({
  totalUsers: 0,
  totalPatients: 0,
  lowStockItems: 0,
  pendingInvoices: 0
});

async function loadStats() {
  try {
    const [usersRes, patientsRes, lowStockRes, invoicesRes] = await Promise.all([
      api.get('/api/auth/users/').catch(() => ({ data: [] })),
      api.get('/api/patients/').catch(() => ({ data: [] })),
      api.get('/api/pharmacy/medicines/low_stock/').catch(() => ({ data: [] })),
      api.get('/api/invoices/?status=DUE').catch(() => ({ data: [] }))
    ]);

    stats.value.totalUsers = usersRes.data.length || 0;
    stats.value.totalPatients = patientsRes.data.length || 0;
    stats.value.lowStockItems = lowStockRes.data.length || 0;
    stats.value.pendingInvoices = invoicesRes.data.length || 0;
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

onMounted(() => {
  loadStats();
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
  color: inherit;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  border: 2px solid transparent;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
  border-color: #3498db;
}

.action-icon {
  font-size: 2.5em;
  margin-bottom: 10px;
}

.action-title {
  font-size: 1.2em;
  font-weight: bold;
  margin-bottom: 8px;
  color: #2c3e50;
}

.action-desc {
  color: #7f8c8d;
  font-size: 0.9em;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.module-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 30px;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.2s, box-shadow 0.2s;
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.25);
}

.module-card:nth-child(2) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.module-card:nth-child(3) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.module-card:nth-child(4) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.module-card:nth-child(5) {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.module-card:nth-child(6) {
  background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
}

.module-card h3 {
  margin: 0 0 10px 0;
  font-size: 1.4em;
}

.module-card p {
  margin: 0;
  opacity: 0.9;
  font-size: 0.95em;
}
</style>
