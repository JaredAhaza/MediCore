<template>
  <div>
    <div class="card">
      <h3>Stock Management</h3>
      <p>Add or remove stock from inventory</p>
    </div>

    <div class="card">
      <h4>Add/Remove Stock</h4>
      <form @submit.prevent="submitTransaction">
        <div style="display: grid; gap: 15px;">
          <div>
            <label>Medicine *</label>
            <select v-model="transaction.medicine" required @change="onMedicineSelect">
              <option value="">Select Medicine</option>
              <option v-for="med in medicines" :key="med.id" :value="med.id">
                {{ med.name }} (Current Stock: {{ med.current_stock }})
              </option>
            </select>
          </div>

          <div v-if="selectedMedicine" class="info-box">
            <strong>{{ selectedMedicine.name }}</strong><br />
            Current Stock: <strong>{{ selectedMedicine.current_stock }}</strong> | 
            Reorder Level: {{ selectedMedicine.reorder_level }}
          </div>

          <div>
            <label>Transaction Type *</label>
            <select v-model="transaction.transaction_type" required>
              <option value="">Select Type</option>
              <option value="STOCK_IN">Stock In (Add)</option>
              <option value="STOCK_OUT">Stock Out (Remove)</option>
              <option value="ADJUSTMENT">Adjustment</option>
            </select>
          </div>

          <div>
            <label>Quantity *</label>
            <input v-model.number="transaction.quantity" type="number" min="1" required />
          </div>

          <div>
            <label>Batch Number</label>
            <input v-model="transaction.batch_number" />
          </div>

          <div>
            <label>Expiry Date</label>
            <input v-model="transaction.expiry_date" type="date" />
          </div>

          <div>
            <label>Notes</label>
            <textarea v-model="transaction.notes" rows="3" placeholder="Optional notes about this transaction"></textarea>
          </div>

          <div style="display: flex; gap: 10px;">
            <button type="submit" class="btn">Submit Transaction</button>
            <button type="button" @click="resetForm" class="btn btn-secondary">Reset</button>
          </div>

          <div v-if="message" :style="messageStyle">
            {{ message }}
          </div>
        </div>
      </form>
    </div>

    <div class="card">
      <h4>Recent Transactions</h4>
      <div v-for="trans in recentTransactions" :key="trans.id" style="padding: 10px; border-bottom: 1px solid #eee;">
        <div style="display: flex; justify-content: space-between;">
          <div>
            <strong>{{ trans.medicine_name }}</strong>
            <span :style="getTransactionBadge(trans.transaction_type)">
              {{ trans.transaction_type }}
            </span>
          </div>
          <div>
            <strong>{{ trans.transaction_type.includes('IN') ? '+' : '-' }}{{ trans.quantity }}</strong>
          </div>
        </div>
        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
          {{ new Date(trans.created_at).toLocaleString() }} • By: {{ trans.created_by_name }}
        </div>
        <div v-if="trans.notes" style="font-size: 0.85em; color: #666; font-style: italic;">
          {{ trans.notes }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api/client';

const medicines = ref([]);
const recentTransactions = ref([]);
const selectedMedicine = ref(null);
const message = ref('');
const messageType = ref('');

const transaction = ref({
  medicine: '',
  transaction_type: '',
  quantity: 1,
  batch_number: '',
  expiry_date: '',
  notes: ''
});

const messageStyle = computed(() => ({
  padding: '10px',
  borderRadius: '4px',
  background: messageType.value === 'success' ? '#d4edda' : '#f8d7da',
  color: messageType.value === 'success' ? '#155724' : '#721c24',
  border: `1px solid ${messageType.value === 'success' ? '#c3e6cb' : '#f5c6cb'}`
}));

async function loadMedicines() {
  const { data } = await api.get('/api/pharmacy/medicines/');
  medicines.value = data;
}

async function loadRecentTransactions() {
  const { data } = await api.get('/api/pharmacy/inventory-transactions/');
  recentTransactions.value = data.slice(0, 10);
}

function onMedicineSelect() {
  selectedMedicine.value = medicines.value.find(m => m.id === parseInt(transaction.value.medicine));
}

async function submitTransaction() {
  try {
    message.value = '';
    const endpoint = transaction.value.transaction_type === 'STOCK_IN' 
      ? '/api/pharmacy/inventory-transactions/stock_in/'
      : transaction.value.transaction_type === 'STOCK_OUT'
        ? '/api/pharmacy/inventory-transactions/stock_out/'
        : '/api/pharmacy/inventory-transactions/';
    
    await api.post(endpoint, transaction.value);
    
    message.value = 'Transaction completed successfully!';
    messageType.value = 'success';
    
    resetForm();
    await Promise.all([loadMedicines(), loadRecentTransactions()]);
    
    setTimeout(() => { message.value = ''; }, 3000);
  } catch (error) {
    message.value = error.response?.data?.error || 'Failed to submit transaction';
    messageType.value = 'error';
  }
}

function resetForm() {
  transaction.value = {
    medicine: '',
    transaction_type: '',
    quantity: 1,
    batch_number: '',
    expiry_date: '',
    notes: ''
  };
  selectedMedicine.value = null;
}

function getTransactionBadge(type) {
  const colors = {
    STOCK_IN: 'background: #00b894; color: white;',
    STOCK_OUT: 'background: #d63031; color: white;',
    DISPENSED: 'background: #0984e3; color: white;',
    ADJUSTMENT: 'background: #fdcb6e; color: #333;'
  };
  return `padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 10px; ${colors[type] || ''}`;
}

onMounted(() => {
  loadMedicines();
  loadRecentTransactions();
});
</script>

<style scoped>
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
input, select, textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.btn {
  padding: 10px 20px;
  background: #0984e3;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}
.btn-secondary {
  background: #636e72;
}
.btn:hover {
  opacity: 0.9;
}
.info-box {
  padding: 15px;
  background: #e3f2fd;
  border-left: 4px solid #0984e3;
  border-radius: 4px;
}
</style>
