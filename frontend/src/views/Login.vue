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

	<!-- Password Change Modal -->
	<ChangePasswordModal 
		:show="showPasswordModal" 
		:isRequired="true"
		@success="handlePasswordChanged"
	/>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import ChangePasswordModal from "../components/ChangePasswordModal.vue";

const auth = useAuthStore();
const username = ref("");
const password = ref("");
const route = useRoute();
const router = useRouter();
const showPasswordModal = ref(false);

async function onSubmit() {
	const ok = await auth.login(username.value, password.value);
	if (ok) {
		// Check if password change is required
		if (auth.user?.password_change_required) {
			showPasswordModal.value = true;
		} else {
			router.push(route.query.next ? String(route.query.next) : "/dashboard");
		}
	}
}

async function handlePasswordChanged() {
	showPasswordModal.value = false;
	// Refresh user data to get updated password_change_required status
	await auth.fetchMe();
	// Redirect to dashboard
	router.push(route.query.next ? String(route.query.next) : "/dashboard");
}
</script>
