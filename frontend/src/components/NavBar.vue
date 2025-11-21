<template>
        <nav>
                <div class="container" style="display:flex; align-items:center; gap:1rem;">
                        <RouterLink to="/" class="brand">🏥 MediCore</RouterLink>
                        
                        <!-- Admin Navigation -->
                        <template v-if="auth.access && auth.user?.role === 'ADMIN'">
                                <RouterLink to="/admin/dashboard">Dashboard</RouterLink>
                                <RouterLink to="/admin/users">Users</RouterLink>
                                <RouterLink to="/patients">Patients</RouterLink>
                                <RouterLink to="/pharmacy">Pharmacy</RouterLink>
                                <RouterLink to="/finance">Finance</RouterLink>
                        </template>
                        
                        <!-- Pharmacist Navigation -->
                        <template v-else-if="auth.access && auth.user?.role === 'PHARMACIST'">
                                <RouterLink to="/pharmacist/dashboard">Dashboard</RouterLink>
                                <RouterLink to="/emr/prescriptions">Prescriptions</RouterLink>
                                <RouterLink to="/pharmacy/dispense">Dispense</RouterLink>
                                <RouterLink to="/pharmacy/medicines">Medicines</RouterLink>
                                <RouterLink to="/finance/invoices">Invoices</RouterLink>
                        </template>
                        
                        <!-- Other Roles Navigation -->
                        <template v-else-if="auth.access">
                                <RouterLink to="/patients">Patients</RouterLink>
                                <RouterLink to="/emr/treatment-notes">Treatment Notes</RouterLink>
                                <RouterLink to="/pharmacy">Pharmacy</RouterLink>
                        </template>
                        
                        <span style="margin-left:auto;"></span>
                        
                        <!-- User Menu -->
                        <RouterLink to="/me" v-if="auth.access" class="user-link">
                                <span class="user-icon">👤</span>
                                {{ auth.user?.username }}
                        </RouterLink>
                        <button v-if="auth.access" @click="logout" class="logout-btn">Logout</button>
                        <RouterLink to="/login" v-else class="login-btn">Login</RouterLink>
                </div>
        </nav>
</template>

<script setup>
import { useAuthStore } from "../stores/auth";
import { RouterLink, useRouter } from "vue-router";

const auth = useAuthStore();
const router = useRouter();
function logout() { auth.logout(); router.push({ name: "Landing" }); }
</script>

<style scoped>
nav {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem 20px;
}

.brand {
        font-size: 1.3em;
        font-weight: bold;
        color: white !important;
        text-decoration: none;
        margin-right: 1rem;
}

a {
        color: rgba(255,255,255,0.9);
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: all 0.2s;
        font-weight: 500;
}

a:hover {
        background: rgba(255,255,255,0.15);
        color: white;
}

a.router-link-active {
        background: rgba(255,255,255,0.2);
        color: white;
        font-weight: 600;
}

.user-link {
        display: flex;
        align-items: center;
        gap: 0.5rem;
}

.user-icon {
        font-size: 1.2em;
}

button {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s;
}

button:hover {
        background: rgba(255,255,255,0.3);
        border-color: rgba(255,255,255,0.5);
}

.login-btn {
        background: white;
        color: #667eea;
        font-weight: 600;
}

.login-btn:hover {
        background: rgba(255,255,255,0.9);
        color: #764ba2;
}
</style>
