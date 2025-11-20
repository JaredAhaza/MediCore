<template>
	<div>
		<div class="card">
			<div class="card-header">
				<h3>Patients</h3>
				<button class="btn" type="button" @click="voiceInsights" :disabled="speaking">
					{{ speaking ? 'Speaking…' : 'Voice Insights' }}
				</button>
			</div>
			<input v-model="q" placeholder="Search by name, medical ID or national ID" @input="debouncedLoad" />
		</div>
		<div class="card filters-card">
			<div class="filter-group">
				<label>Gender</label>
				<select v-model="filters.gender">
					<option value="">All</option>
					<option value="M">Male</option>
					<option value="F">Female</option>
					<option value="O">Other</option>
				</select>
			</div>
			<div class="filter-group">
				<label>National ID</label>
				<select v-model="filters.nationalId">
					<option value="any">All Patients</option>
					<option value="with">With National ID</option>
					<option value="without">Without National ID</option>
				</select>
			</div>
			<div class="filter-group">
				<label>Pending Prescriptions</label>
				<select v-model="filters.pending">
					<option value="any">All Patients</option>
					<option value="pending">Has Pending</option>
					<option value="nonpending">None Pending</option>
				</select>
			</div>
			<div class="filter-summary">
				Showing {{ filteredPatients.length }} of {{ patients.length }} patients
			</div>
		</div>

		<div v-for="p in filteredPatients" :key="p.id" class="card" style="display: flex; justify-content: space-between; align-items: center;">
			<div style="flex: 1;">
				<b>{{ p.name }}</b> — {{ p.medical_id }}
				<div style="font-size:.9em; color:#666;">{{ p.gender }} • {{ p.dob }}</div>
				<div v-if="p.national_id" style="font-size:0.85em; color:#2d3436; margin-top:4px;">
					National ID: {{ p.national_id }}
				</div>
			</div>
			<div style="text-align: right; display: flex; gap: 8px; align-items: center; justify-content: flex-end;">
				<router-link 
					:to="{
						name: 'PrescriptionCreate',
						query: {
							patient_username: p.username,
							patient_id: p.id,
							patient_name: p.name,
							patient_medical_id: p.medical_id,
							patient_national_id: p.national_id,
							patient_gender: p.gender,
							patient_dob: p.dob,
							patient_contact: p.contact
						}
					}" 
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
import { computed, reactive, ref } from "vue";
import api from "../api/client";
import { useVoiceInsights } from "@/composables/useVoiceInsights";
let timer;
const q = ref("");
const patients = ref([]);
const filters = reactive({
	gender: "",
	nationalId: "any",
	pending: "any",
});
const filteredPatients = computed(() => {
	return patients.value.filter((patient) => {
		if (filters.gender) {
			const normalized = (patient.gender || "").toUpperCase();
			if (normalized !== filters.gender) return false;
		}
		if (filters.nationalId === "with" && !patient.national_id) return false;
		if (filters.nationalId === "without" && patient.national_id) return false;
		if (filters.pending === "pending" && !hasPendingPrescription(patient.username)) return false;
		if (filters.pending === "nonpending" && hasPendingPrescription(patient.username)) return false;
		return true;
	});
});

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
		const missingNationalId = patients.value.filter(p => !p.national_id).length;

		const parts = [
			`There are ${total} patients in the registry.`,
			genderSummary ? `Gender split: ${genderSummary}.` : '',
			avgAge ? `Average age is ${avgAge} years with youngest at ${youngest} and oldest at ${oldest}.` : '',
			pendingCount ? `${pendingCount} patients have pending prescriptions requiring follow up.` : 'No patients have pending prescriptions right now.',
			missingNationalId
				? `${missingNationalId} patients still need national IDs recorded for compliance.`
				: 'All patients have national IDs on record.',
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

.filters-card {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	gap: 12px;
	align-items: end;
}

.filter-group label {
	display: block;
	margin-bottom: 4px;
	font-weight: 600;
	color: #2d3436;
}

.filter-group select {
	width: 100%;
	padding: 6px 8px;
	border: 1px solid #dfe6e9;
	border-radius: 4px;
}

.filter-summary {
	font-size: 0.9em;
	color: #636e72;
	align-self: center;
}
</style>
