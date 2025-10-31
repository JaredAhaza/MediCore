<template>
  <div>
    <div class="card">
      <h3>{{ isEdit ? 'Edit Medicine' : 'Add New Medicine' }}</h3>
      <form @submit.prevent="save">
        <div style="display: grid; gap: 15px;">
          <div>
            <label>Medicine Name *</label>
            <input v-model="form.name" required />
          </div>

          <div>
            <label>Generic Name</label>
            <input v-model="form.generic_name" />
          </div>

          <div>
            <label>Category *</label>
            <select v-model="form.category" required>
              <option value="">Select Category</option>
              <option value="TABLET">Tablet</option>
              <option value="CAPSULE">Capsule</option>
              <option value="SYRUP">Syrup</option>
              <option value="INJECTION">Injection</option>
              <option value="CREAM">Cream/Ointment</option>
              <option value="DROPS">Drops</option>
              <option value="INHALER">Inhaler</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div>
            <label>Manufacturer</label>
            <input v-model="form.manufacturer" />
          </div>

          <div>
            <label>Description</label>
            <textarea v-model="form.description" rows="3"></textarea>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
              <label>Reorder Level *</label>
              <input v-model.number="form.reorder_level" type="number" min="0" required />
            </div>

            <div>
              <label>Unit Price ($) *</label>
              <input v-model.number="form.unit_price" type="number" step="0.01" min="0" required />
            </div>
          </div>

          <div>
            <label>
              <input type="checkbox" v-model="form.is_active" />
              Active
            </label>
          </div>

          <div style="display: flex; gap: 10px;">
            <button type="submit" class="btn">{{ isEdit ? 'Update' : 'Create' }} Medicine</button>
            <router-link to="/pharmacy/medicines" class="btn btn-secondary">Cancel</router-link>
          </div>

          <div v-if="error" style="color: red; margin-top: 10px;">
            {{ error }}
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api/client';

const route = useRoute();
const router = useRouter();
const isEdit = ref(false);
const error = ref('');

const form = ref({
  name: '',
  generic_name: '',
  category: '',
  manufacturer: '',
  description: '',
  reorder_level: 10,
  unit_price: 0,
  is_active: true
});

async function save() {
  try {
    error.value = '';
    if (isEdit.value) {
      await api.put(`/api/pharmacy/medicines/${route.params.id}/`, form.value);
    } else {
      await api.post('/api/pharmacy/medicines/', form.value);
    }
    router.push('/pharmacy/medicines');
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save medicine';
  }
}

onMounted(async () => {
  if (route.params.id) {
    isEdit.value = true;
    const { data } = await api.get(`/api/pharmacy/medicines/${route.params.id}/`);
    form.value = data;
  }
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
</style>
