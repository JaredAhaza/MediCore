<template>
  <div class="container">
    <div class="header">
      <h1>Register New User</h1>
      <router-link to="/admin/users" class="btn-back">
        ← Back to Users
      </router-link>
    </div>

    <div class="form-card">
      <form @submit.prevent="handleSubmit">
        <!-- Personal Information -->
        <div class="form-section">
          <h2>Personal Information</h2>
          <div class="form-row">
            <div class="form-group">
              <label for="first_name">First Name *</label>
              <input
                id="first_name"
                v-model="form.first_name"
                type="text"
                required
                placeholder="Enter first name"
              />
            </div>
            <div class="form-group">
              <label for="last_name">Last Name *</label>
              <input
                id="last_name"
                v-model="form.last_name"
                type="text"
                required
                placeholder="Enter last name"
              />
            </div>
          </div>
        </div>

        <!-- Account Information -->
        <div class="form-section">
          <h2>Account Information</h2>
          <div class="form-row">
            <div class="form-group">
              <label for="username">Username *</label>
              <input
                id="username"
                v-model="form.username"
                type="text"
                required
                placeholder="Enter username"
              />
            </div>
            <div class="form-group">
              <label for="email">Email *</label>
              <input
                id="email"
                v-model="form.email"
                type="email"
                required
                placeholder="Enter email address"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="role">Role *</label>
            <select id="role" v-model="form.role" required>
              <option value="">Select a role</option>
              <option value="ADMIN">Admin</option>
              <option value="DOCTOR">Doctor</option>
              <option value="LAB_TECH">Lab Tech</option>
              <option value="PHARMACIST">Pharmacist</option>
              <option value="FINANCE">Finance</option>
            </select>
            <div class="role-description" v-if="form.role">
              {{ getRoleDescription(form.role) }}
            </div>
          </div>
        </div>

        <!-- Password -->
        <div class="form-section">
          <h2>Password</h2>
          <div class="form-row">
            <div class="form-group">
              <label for="password">Password *</label>
              <input
                id="password"
                v-model="form.password"
                type="password"
                required
                placeholder="Enter password"
                minlength="8"
              />
              <small class="help-text">Minimum 8 characters</small>
            </div>
            <div class="form-group">
              <label for="password_confirm">Confirm Password *</label>
              <input
                id="password_confirm"
                v-model="form.password_confirm"
                type="password"
                required
                placeholder="Confirm password"
              />
            </div>
          </div>
          <div v-if="passwordMismatch" class="error-text">
            Passwords do not match
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Success Message -->
        <div v-if="success" class="success-message">
          User registered successfully! Redirecting...
        </div>

        <!-- Actions -->
        <div class="form-actions">
          <router-link to="/admin/users" class="btn btn-secondary">
            Cancel
          </router-link>
          <button type="submit" class="btn btn-primary" :disabled="loading || passwordMismatch">
            <span v-if="loading">Registering...</span>
            <span v-else>Register User</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/client';

const router = useRouter();

const form = ref({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  role: '',
  password: '',
  password_confirm: ''
});

const loading = ref(false);
const error = ref(null);
const success = ref(false);

const passwordMismatch = computed(() => {
  return form.value.password && form.value.password_confirm && 
         form.value.password !== form.value.password_confirm;
});

function getRoleDescription(role) {
  const descriptions = {
    'ADMIN': 'Full system access including user management',
    'DOCTOR': 'Access to patient records, prescriptions, and treatment notes',
    'LAB_TECH': 'Access to lab reports and patient records',
    'PHARMACIST': 'Access to pharmacy inventory, dispensing, and invoicing',
    'FINANCE': 'Access to billing, payments, and financial reports'
  };
  return descriptions[role] || '';
}

async function handleSubmit() {
  if (passwordMismatch.value) {
    error.value = 'Passwords do not match';
    return;
  }

  loading.value = true;
  error.value = null;
  success.value = false;

  try {
    await api.post('/api/auth/users/', form.value);
    success.value = true;
    
    // Redirect after 1.5 seconds
    setTimeout(() => {
      router.push('/admin/users');
    }, 1500);
  } catch (err) {
    console.error('Error registering user:', err);
    
    if (err.response?.data) {
      // Handle validation errors
      const errors = err.response.data;
      if (typeof errors === 'object') {
        const errorMessages = Object.entries(errors)
          .map(([field, messages]) => {
            const fieldName = field.replace('_', ' ');
            const message = Array.isArray(messages) ? messages[0] : messages;
            return `${fieldName}: ${message}`;
          })
          .join(', ');
        error.value = errorMessages;
      } else {
        error.value = errors.detail || 'Failed to register user';
      }
    } else {
      error.value = 'Failed to register user. Please try again.';
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.container {
  max-width: 900px;
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

.btn-back {
  color: #3498db;
  text-decoration: none;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 6px;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #ecf0f1;
}

.form-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.form-section {
  margin-bottom: 35px;
}

.form-section h2 {
  font-size: 1.3em;
  margin: 0 0 20px 0;
  color: #2c3e50;
  padding-bottom: 10px;
  border-bottom: 2px solid #ecf0f1;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1em;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3498db;
}

.help-text {
  display: block;
  margin-top: 5px;
  font-size: 0.85em;
  color: #7f8c8d;
}

.role-description {
  margin-top: 8px;
  padding: 12px;
  background: #e8f4f8;
  border-left: 4px solid #3498db;
  border-radius: 4px;
  font-size: 0.9em;
  color: #2c3e50;
}

.error-text {
  color: #e74c3c;
  font-size: 0.9em;
  margin-top: 5px;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #c33;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #28a745;
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #ecf0f1;
}

.btn {
  padding: 12px 30px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  border: none;
  cursor: pointer;
  font-size: 1em;
  transition: all 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

.btn-primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background: #bdc3c7;
}
</style>
