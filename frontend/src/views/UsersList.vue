<template>
  <div class="container">
    <div class="header">
      <h1>User Management</h1>
      <router-link to="/admin/users/new" class="btn btn-primary">
        <span class="icon">➕</span> Register New User
      </router-link>
    </div>

    <!-- Filters -->
    <div class="filters">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search by username, email, or name..." 
        class="search-input"
        @input="filterUsers"
      />
      <select v-model="roleFilter" @change="filterUsers" class="filter-select">
        <option value="">All Roles</option>
        <option value="ADMIN">Admin</option>
        <option value="DOCTOR">Doctor</option>
        <option value="LAB_TECH">Lab Tech</option>
        <option value="PHARMACIST">Pharmacist</option>
        <option value="FINANCE">Finance</option>
        <option value="PATIENT">Patient</option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">Loading users...</div>

    <!-- Error State -->
    <div v-if="error" class="error-message">{{ error }}</div>

    <!-- Users Table -->
    <div v-if="!loading && !error" class="table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Joined</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>
              <div class="user-username">
                <span class="username-icon">👤</span>
                {{ user.username }}
              </div>
            </td>
            <td>{{ user.first_name }} {{ user.last_name }}</td>
            <td>{{ user.email || '-' }}</td>
            <td>
              <span :class="['role-badge', `role-${user.role.toLowerCase()}`]">
                {{ getRoleLabel(user.role) }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', user.is_active ? 'status-active' : 'status-inactive']">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>{{ formatDate(user.date_joined) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredUsers.length === 0" class="no-results">
        No users found matching your criteria.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api/client';

const users = ref([]);
const loading = ref(true);
const error = ref(null);
const searchQuery = ref('');
const roleFilter = ref('');

const filteredUsers = computed(() => {
  let result = users.value;

  // Filter by role
  if (roleFilter.value) {
    result = result.filter(user => user.role === roleFilter.value);
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(user => 
      user.username.toLowerCase().includes(query) ||
      user.email?.toLowerCase().includes(query) ||
      user.first_name?.toLowerCase().includes(query) ||
      user.last_name?.toLowerCase().includes(query)
    );
  }

  return result;
});

async function loadUsers() {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.get('/api/auth/users/');
    users.value = response.data;
  } catch (err) {
    error.value = 'Failed to load users. Please try again.';
    console.error('Error loading users:', err);
  } finally {
    loading.value = false;
  }
}

function filterUsers() {
  // Trigger computed property recalculation
}

function getRoleLabel(role) {
  const labels = {
    'ADMIN': 'Admin',
    'DOCTOR': 'Doctor',
    'LAB_TECH': 'Lab Tech',
    'PHARMACIST': 'Pharmacist',
    'FINANCE': 'Finance',
    'PATIENT': 'Patient'
  };
  return labels[role] || role;
}

function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
}

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2em;
  margin: 0;
  color: #2c3e50;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

.icon {
  font-size: 1.2em;
}

.filters {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1em;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
}

.filter-select {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1em;
  background: white;
  cursor: pointer;
  min-width: 180px;
}

.filter-select:focus {
  outline: none;
  border-color: #3498db;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
  font-size: 1.2em;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #c33;
}

.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background: #f8f9fa;
}

.users-table th {
  padding: 16px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #e0e0e0;
}

.users-table td {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.users-table tbody tr:hover {
  background: #f8f9fa;
}

.user-username {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #2c3e50;
}

.username-icon {
  font-size: 1.2em;
}

.role-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 600;
  text-transform: uppercase;
}

.role-admin {
  background: #e74c3c;
  color: white;
}

.role-doctor {
  background: #3498db;
  color: white;
}

.role-lab_tech {
  background: #9b59b6;
  color: white;
}

.role-pharmacist {
  background: #2ecc71;
  color: white;
}

.role-finance {
  background: #f39c12;
  color: white;
}

.role-patient {
  background: #95a5a6;
  color: white;
}

.status-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 600;
}

.status-active {
  background: #d4edda;
  color: #155724;
}

.status-inactive {
  background: #f8d7da;
  color: #721c24;
}

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
  font-size: 1.1em;
}
</style>
