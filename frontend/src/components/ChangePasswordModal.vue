<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-card">
      <div class="modal-header">
        <h2>{{ isRequired ? '⚠️ Password Change Required' : 'Change Password' }}</h2>
        <button v-if="!isRequired" @click="close" class="close-btn">✕</button>
      </div>

      <div v-if="isRequired" class="alert-message">
        <p>Your password is temporary. Please change it to continue.</p>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="old_password">Current Password *</label>
          <input
            id="old_password"
            v-model="form.old_password"
            type="password"
            required
            placeholder="Enter current password"
            autocomplete="current-password"
          />
        </div>

        <div class="form-group">
          <label for="new_password">New Password *</label>
          <input
            id="new_password"
            v-model="form.new_password"
            type="password"
            required
            placeholder="Enter new password"
            minlength="8"
            autocomplete="new-password"
          />
          <small class="help-text">Minimum 8 characters, must be different from current password</small>
        </div>

        <div class="form-group">
          <label for="new_password_confirm">Confirm New Password *</label>
          <input
            id="new_password_confirm"
            v-model="form.new_password_confirm"
            type="password"
            required
            placeholder="Confirm new password"
            autocomplete="new-password"
          />
        </div>

        <div v-if="passwordMismatch" class="error-text">
          Passwords do not match
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          Password changed successfully!
        </div>

        <div class="form-actions">
          <button v-if="!isRequired" type="button" @click="close" class="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading || passwordMismatch">
            <span v-if="loading">Changing...</span>
            <span v-else>Change Password</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import api from '../api/client';

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  isRequired: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close', 'success']);

const form = ref({
  old_password: '',
  new_password: '',
  new_password_confirm: ''
});

const loading = ref(false);
const error = ref(null);
const success = ref(false);

const passwordMismatch = computed(() => {
  return form.value.new_password && form.value.new_password_confirm && 
         form.value.new_password !== form.value.new_password_confirm;
});

// Reset form when modal is closed
watch(() => props.show, (newVal) => {
  if (!newVal) {
    form.value = {
      old_password: '',
      new_password: '',
      new_password_confirm: ''
    };
    error.value = null;
    success.value = false;
  }
});

async function handleSubmit() {
  if (passwordMismatch.value) {
    error.value = 'Passwords do not match';
    return;
  }

  loading.value = true;
  error.value = null;
  success.value = false;

  try {
    await api.post('/api/auth/users/change_password/', {
      old_password: form.value.old_password,
      new_password: form.value.new_password,
      new_password_confirm: form.value.new_password_confirm
    });
    
    success.value = true;
    
    // Close modal and emit success after 1 second
    setTimeout(() => {
      emit('success');
      close();
    }, 1000);
  } catch (err) {
    console.error('Error changing password:', err);
    
    if (err.response?.data) {
      const errors = err.response.data;
      if (typeof errors === 'object') {
        // Handle specific field errors
        if (errors.old_password) {
          error.value = errors.old_password;
        } else if (errors.new_password) {
          error.value = Array.isArray(errors.new_password) ? errors.new_password[0] : errors.new_password;
        } else {
          const errorMessages = Object.entries(errors)
            .map(([field, messages]) => {
              const message = Array.isArray(messages) ? messages[0] : messages;
              return message;
            })
            .join(', ');
          error.value = errorMessages;
        }
      } else {
        error.value = errors.message || errors.detail || 'Failed to change password';
      }
    } else {
      error.value = 'Failed to change password. Please try again.';
    }
  } finally {
    loading.value = false;
  }
}

function close() {
  if (!props.isRequired) {
    emit('close');
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-card {
  background: white;
  border-radius: 16px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 30px;
  border-bottom: 2px solid #ecf0f1;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5em;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5em;
  color: #7f8c8d;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #ecf0f1;
  color: #2c3e50;
}

.alert-message {
  background: #fff3cd;
  border-left: 4px solid #f39c12;
  padding: 15px 30px;
  margin: 0;
}

.alert-message p {
  margin: 0;
  color: #856404;
  font-weight: 500;
}

form {
  padding: 30px;
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

.form-group input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1em;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.help-text {
  display: block;
  margin-top: 5px;
  font-size: 0.85em;
  color: #7f8c8d;
}

.error-text {
  color: #e74c3c;
  font-size: 0.9em;
  margin-bottom: 15px;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #c33;
  font-size: 0.9em;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #28a745;
  font-size: 0.9em;
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  margin-top: 25px;
  padding-top: 20px;
  border-top: 2px solid #ecf0f1;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 1em;
  font-weight: 600;
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
