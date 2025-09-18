<template>
	<div class="card">
		<h3>My Profile</h3>
		<div v-if="auth.user">
			<p><b>Username:</b> {{ auth.user.username }}</p>
			<p><b>Email:</b> {{ auth.user.email }}</p>
			<p><b>Role:</b> {{ auth.user.role }}</p>
		</div>
	</div>
</template>

<script setup>
import { useAuthStore } from "../stores/auth";
const auth = useAuthStore();
</script>
