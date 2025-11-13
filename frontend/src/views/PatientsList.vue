<template>
	<div>
		<div class="card">
			<h3>Patients</h3>
			<input v-model="q" placeholder="Search by name or medical ID" @input="debouncedLoad" />
		</div>
		<div v-for="p in patients" :key="p.id" class="card" style="display: flex; justify-content: space-between; align-items: center;">
			<div style="flex: 1;">
				<b>{{ p.name }}</b> — {{ p.medical_id }}
				<div style="font-size:.9em; color:#666;">{{ p.gender }} • {{ p.dob }}</div>
			</div>
			<div style="text-align: right; display: flex; gap: 8px; align-items: center; justify-content: flex-end;">
				<router-link 
					:to="{ name: 'PrescriptionCreate', query: { patient_username: p.username } }" 
					class="btn"
					v-if="p.username"
				>
					Add Prescription
				</router-link>

				<router-link
					v-if="p.username && hasPendingPrescription(p.username)"
					:to="{ name: 'PrescriptionsList', query: { patient: p.username } }"
					class="btn secondary"
				>
					View Prescription
				</router-link>

				<span v-else-if="!p.username" style="color:#999; font-size:0.85em;">No username</span>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import api from "../api/client";
let timer;
const q = ref("");
const patients = ref([]);
// Track usernames of patients with at least one pending prescription
const pendingUsernames = ref(new Set());

async function load() {
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/patients/", { params });
	patients.value = data;

	// Refresh pending prescriptions list in the background
	refreshPending();
}
function debouncedLoad() {
	clearTimeout(timer);
	timer = setTimeout(load, 250);
}
async function refreshPending() {
	try {
		const { data } = await api.get("/api/prescriptions/");
		const set = new Set(
			(data || [])
				.filter(p => p.status === 'PENDING' && p.patient_detail && p.patient_detail.username)
				.map(p => p.patient_detail.username)
		);
		pendingUsernames.value = set;
	} catch (e) {
		console.error('Failed to load pending prescriptions', e);
	}
}

function hasPendingPrescription(username) {
	return pendingUsernames.value.has(username);
}

load();
// Initial pending fetch
refreshPending();
</script>

<style scoped>
.btn {
	padding: 8px 16px;
	background: #0984e3;
	color: white;
	text-decoration: none;
	border-radius: 4px;
	font-size: 0.9em;
	display: inline-block;
}
.btn:hover {
	background: #0652a3;
}
.btn.secondary {
	background: #636e72;
}
.btn.secondary:hover {
	background: #2d3436;
}
</style>
