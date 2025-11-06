<template>
        <nav>
                <div class="container" style="display:flex; align-items:center; gap:1rem;">
                        <RouterLink to="/">MediCore</RouterLink>
                        <RouterLink to="/patients" v-if="auth.access">Patients</RouterLink>
                        <RouterLink to="/patients/new" v-if="auth.access && auth.hasWriteRole()">New Patient</RouterLink>
                        <RouterLink to="/emr/treatment-notes" v-if="auth.access">Treatment Notes</RouterLink>
                        <RouterLink to="/pharmacy" v-if="auth.access">Pharmacy</RouterLink>
                        <span style="margin-left:auto;"></span>
                        <RouterLink to="/me" v-if="auth.access">{{ auth.user?.username }}</RouterLink>
                        <button v-if="auth.access" @click="logout">Logout</button>
                        <RouterLink to="/login" v-else>Login</RouterLink>
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
