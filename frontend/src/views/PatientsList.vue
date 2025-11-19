<template>
	<div>
		<div class="card">
			<div class="card-header">
				<h3>Patients</h3>
				<button class="btn" type="button" @click="voiceInsights" :disabled="speaking">
					{{ speaking ? 'Speaking…' : 'Voice Insights' }}
				</button>
			</div>
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
import { useVoiceInsights } from "@/composables/useVoiceInsights";
let timer;
const q = ref("");
const patients = ref([]);
// Track usernames of patients with at least one pending prescription
const pendingUsernames = ref(new Set());
const { speaking, speakInsights } = useVoiceInsights();

async function load(options = {}) {
	const { alsoRefreshPending = true } = options;
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/patients/", { params });
	patients.value = data;

	// Refresh pending prescriptions list in the background
	if (alsoRefreshPending) refreshPending();
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

function calculateAge(dob) {
	if (!dob) return null;
	const date = new Date(dob);
	if (Number.isNaN(date.getTime())) return null;
	const today = new Date();
	let age = today.getFullYear() - date.getFullYear();
	const m = today.getMonth() - date.getMonth();
	if (m < 0 || (m === 0 && today.getDate() < date.getDate())) age--;
	return age;
}

async function voiceInsights() {
	try {
		await Promise.all([load({ alsoRefreshPending: false }), refreshPending()]);
		const total = patients.value.length;
		if (!total) {
			alert("No patients available yet.");
			return;
		}
		const genderCounts = patients.value.reduce((acc, patient) => {
			const gender = (patient.gender || "Unspecified").toLowerCase();
			acc[gender] = (acc[gender] || 0) + 1;
			return acc;
		}, {});
		const genderSummary = Object.entries(genderCounts)
			.map(([gender, count]) => `${count} ${gender}`)
			.join(', ');
		const withoutUsername = patients.value.filter(p => !p.username).length;
		const ages = patients.value
			.map(p => calculateAge(p.dob))
			.filter(age => age !== null);
		const avgAge = ages.length
			? Math.round(ages.reduce((sum, val) => sum + val, 0) / ages.length)
			: null;
		const youngest = ages.length ? Math.min(...ages) : null;
		const oldest = ages.length ? Math.max(...ages) : null;
		const pendingCount = pendingUsernames.value.size;

		const parts = [
			`There are ${total} patients in the registry.`,
			genderSummary ? `Gender split: ${genderSummary}.` : '',
			avgAge ? `Average age is ${avgAge} years with youngest at ${youngest} and oldest at ${oldest}.` : '',
			pendingCount ? `${pendingCount} patients have pending prescriptions requiring follow up.` : 'No patients have pending prescriptions right now.',
			withoutUsername
				? `${withoutUsername} patients still need portal usernames for prescription tracking.`
				: 'All patients have portal usernames assigned.'
		].filter(Boolean);

		await speakInsights(parts);
	} catch (err) {
		console.error("Patient voice insights failed", err);
		alert("Unable to generate patient voice insights.");
	}
}
</script>

<style scoped>
.card-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}
.btn {
	padding: 8px 16px;
	background: #0984e3;
	color: white;
	text-decoration: none;
	border-radius: 4px;
	font-size: 0.9em;
	display: inline-block;
	border: none;
	cursor: pointer;
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
.btn:disabled {
	opacity: 0.6;
	cursor: not-allowed;
}
</style>
