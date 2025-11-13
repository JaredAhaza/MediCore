<template>
  <div>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content container">
        <div>
          <h1>MediCore</h1>
          <p class="sub">Streamlined EMR, Patient Management, and Pharmacy Operations</p>
          <div class="cta" v-if="!auth.access">
            <RouterLink to="/login" class="btn primary">Login</RouterLink>
          </div>
          <div class="cta" v-else>
            <span class="welcome">Welcome, {{ auth.user?.username }}</span>
            <RouterLink to="/patients" class="btn">Patients</RouterLink>
            <RouterLink to="/emr/prescriptions" class="btn">EMR</RouterLink>
            <RouterLink to="/pharmacy" class="btn">Pharmacy</RouterLink>
            <button class="btn danger" @click="logout">Logout</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="container" style="margin-top: 1rem;">
      <div class="grid">
        <div class="feature card">
          <h3>Patients</h3>
          <p>Search, register, and manage patient records with ease.</p>
          <div class="actions">
            <RouterLink to="/patients" class="btn">View Patients</RouterLink>
            <RouterLink to="/patients/new" class="btn secondary" v-if="auth.hasWriteRole()">Add Patient</RouterLink>
          </div>
        </div>

        <div class="feature card">
          <h3>EMR</h3>
          <p>Document treatment notes and manage prescriptions securely.</p>
          <div class="actions">
            <RouterLink to="/emr/treatment-notes" class="btn">Treatment Notes</RouterLink>
            <RouterLink to="/emr/prescriptions" class="btn secondary">Prescriptions</RouterLink>
          </div>
        </div>

        <div class="feature card">
          <h3>Pharmacy</h3>
          <p>Monitor inventory, dispense medicine, and process payments.</p>
          <div class="actions">
            <RouterLink to="/pharmacy" class="btn">Dashboard</RouterLink>
            <RouterLink to="/pharmacy/medicines" class="btn secondary">Medicines</RouterLink>
            <RouterLink to="/pharmacy/stock" class="btn secondary">Manage Stock</RouterLink>
          </div>
        </div>
      </div>
  </section>

    <!-- Finance Summary Section -->
    <section class="container" style="margin-top: 1rem;">
      <FinanceSummary />
    </section>
  </div>
  
</template>

<script setup>
import { useAuthStore } from "../stores/auth";
import { useRouter } from "vue-router";
import FinanceSummary from "@/components/FinanceSummary.vue";
const auth = useAuthStore();
const router = useRouter();
function logout() { auth.logout(); router.push({ name: "Landing" }); }
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #0f172a, #1e293b);
  color: #fff;
  padding: 40px 0;
}
.hero-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
h1 {
  margin: 0 0 8px;
  font-size: 2rem;
}
.sub {
  margin: 0 0 16px;
  color: #cbd5e1;
}
.cta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.welcome { margin-right: 8px; color: #e2e8f0; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.feature .actions { display: flex; gap: 8px; flex-wrap: wrap; }

.btn {
  padding: 8px 14px;
  background: #0984e3;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  display: inline-block;
}
.btn:hover { background: #0652a3; }
.btn.secondary { background: #636e72; }
.btn.secondary:hover { background: #2d3436; }
.btn.primary { background: #22c55e; }
.btn.primary:hover { background: #16a34a; }
.btn.danger { background: #ef4444; border: none; }
.btn.danger:hover { background: #dc2626; }
</style>
