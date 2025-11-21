<template>
	<div class="container">
		<div class="profile-card">
			<div class="profile-header">
				<div class="avatar">{{ getInitials() }}</div>
				<div class="profile-info">
					<h2>{{ auth.user?.first_name }} {{ auth.user?.last_name }}</h2>
					<p class="username">@{{ auth.user?.username }}</p>
				</div>
			</div>

			<div class="profile-details">
				<div class="detail-item">
					<span class="label">Email</span>
					<span class="value">{{ auth.user?.email || 'Not set' }}</span>
				</div>
				<div class="detail-item">
					<span class="label">Role</span>
					<span :class="['role-badge', `role-${auth.user?.role?.toLowerCase()}`]">
						{{ getRoleLabel(auth.user?.role) }}
					</span>
				</div>
			</div>

			<div class="profile-actions">
				<button @click="showPasswordModal = true" class="btn btn-primary">
					🔒 Change Password
				</button>
			</div>
		</div>
	</div>

	<!-- Password Change Modal -->
	<ChangePasswordModal 
		:show="showPasswordModal" 
		:isRequired="false"
		@close="showPasswordModal = false"
		@success="handlePasswordChanged"
	/>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from "../stores/auth";
import ChangePasswordModal from "../components/ChangePasswordModal.vue";

const auth = useAuthStore();
const showPasswordModal = ref(false);

function getInitials() {
	const first = auth.user?.first_name?.[0] || '';
	const last = auth.user?.last_name?.[0] || '';
	return (first + last).toUpperCase() || auth.user?.username?.[0]?.toUpperCase() || '?';
}

function getRoleLabel(role) {
	const labels = {
		'ADMIN': 'Admin',
		'DOCTOR': 'Doctor',
		'LAB_TECH': 'Lab Tech',
		'PHARMACIST': 'Pharmacist',
		'FINANCE': 'Finance',
		'PATIENT': 'Patient'
	};
	return labels[role] || role;
}

async function handlePasswordChanged() {
	showPasswordModal.value = false;
	// Refresh user data
	await auth.fetchMe();
}
</script>

<style scoped>
.container {
	max-width: 800px;
	margin: 0 auto;
	padding: 20px;
}

.profile-card {
	background: white;
	border-radius: 16px;
	box-shadow: 0 2px 12px rgba(0,0,0,0.1);
	overflow: hidden;
}

.profile-header {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	padding: 40px 30px;
	display: flex;
	align-items: center;
	gap: 20px;
	color: white;
}

.avatar {
	width: 80px;
	height: 80px;
	border-radius: 50%;
	background: rgba(255,255,255,0.3);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 2em;
	font-weight: bold;
	border: 3px solid rgba(255,255,255,0.5);
}

.profile-info h2 {
	margin: 0 0 5px 0;
	font-size: 1.8em;
}

.username {
	margin: 0;
	opacity: 0.9;
	font-size: 1.1em;
}

.profile-details {
	padding: 30px;
}

.detail-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 15px 0;
	border-bottom: 1px solid #ecf0f1;
}

.detail-item:last-child {
	border-bottom: none;
}

.label {
	font-weight: 600;
	color: #7f8c8d;
	font-size: 0.95em;
}

.value {
	color: #2c3e50;
	font-size: 1.05em;
}

.role-badge {
	display: inline-block;
	padding: 6px 16px;
	border-radius: 20px;
	font-size: 0.9em;
	font-weight: 600;
	text-transform: uppercase;
}

.role-admin {
	background: #e74c3c;
	color: white;
}

.role-doctor {
	background: #3498db;
	color: white;
}

.role-lab_tech {
	background: #9b59b6;
	color: white;
}

.role-pharmacist {
	background: #2ecc71;
	color: white;
}

.role-finance {
	background: #f39c12;
	color: white;
}

.role-patient {
	background: #95a5a6;
	color: white;
}

.profile-actions {
	padding: 30px;
	background: #f8f9fa;
	display: flex;
	gap: 15px;
}

.btn {
	padding: 12px 24px;
	border-radius: 8px;
	border: none;
	cursor: pointer;
	font-size: 1em;
	font-weight: 600;
	transition: all 0.2s;
	display: inline-flex;
	align-items: center;
	gap: 8px;
}

.btn-primary {
	background: #3498db;
	color: white;
}

.btn-primary:hover {
	background: #2980b9;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}
</style>
