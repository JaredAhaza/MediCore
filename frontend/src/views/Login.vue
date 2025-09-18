<template>
	<div class="card" style="max-width:420px;">
		<h3>Login</h3>
		<form @submit.prevent="onSubmit">
			<label>Username</label>
			<input v-model="username" autocomplete="username" />
			<label>Password</label>
			<input v-model="password" type="password" autocomplete="current-password" />
			<button :disabled="auth.loading">{{ auth.loading ? 'Signing in...' : 'Login' }}</button>
			<p v-if="auth.error" style="color:red; margin-top:.5rem;">{{ auth.error }}</p>
		</form>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const username = ref("");
const password = ref("");
const route = useRoute();
const router = useRouter();

async function onSubmit() {
	const ok = await auth.login(username.value, password.value);
	if (ok) {
		router.push(route.query.next ? String(route.query.next) : "/patients");
	}
}
</script>
