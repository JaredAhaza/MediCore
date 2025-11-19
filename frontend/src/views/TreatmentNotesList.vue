<template>
	<div>
		<div class="card">
			<div class="card-header">
				<h3>Treatment Notes</h3>
				<button class="btn" type="button" @click="voiceInsights" :disabled="speaking">
					{{ speaking ? 'Speaking…' : 'Voice Insights' }}
				</button>
			</div>
			<input v-model="q" placeholder="Search by patient or diagnosis" @input="debouncedLoad" />
			<RouterLink v-if="canCreate" to="/emr/treatment-notes/new">New Treatment Note</RouterLink>
		</div>
		<div v-for="n in items" :key="n.id" class="card">
			<b>{{ n.patient_detail?.name }}</b> — {{ n.diagnosis }}
			<div style="font-size:.9em; color:#666;">Doctor: {{ n.doctor }}</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "../stores/auth";
import { RouterLink } from "vue-router";
import api from "../api/client";
import { useVoiceInsights } from "@/composables/useVoiceInsights";

const auth = useAuthStore();
const q = ref("");
const items = ref([]);
const canCreate = ["ADMIN","DOCTOR"].includes(auth.user?.role);
const { speaking, speakInsights } = useVoiceInsights();

async function load() {
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/treatment-notes/", { params });
	items.value = data;
}

let timer;
function debouncedLoad() { clearTimeout(timer); timer = setTimeout(load, 250); }

load();

async function voiceInsights() {
	try {
		await load();
		const total = items.value.length;
		if (!total) {
			alert("No treatment notes available yet.");
			return;
		}
		const diagnosisCounts = items.value.reduce((acc, note) => {
			if (!note.diagnosis) return acc;
			acc[note.diagnosis] = (acc[note.diagnosis] || 0) + 1;
			return acc;
		}, {});
		const doctorCounts = items.value.reduce((acc, note) => {
			if (!note.doctor) return acc;
			acc[note.doctor] = (acc[note.doctor] || 0) + 1;
			return acc;
		}, {});
		const topDiagnosis = Object.entries(diagnosisCounts).sort((a, b) => b[1] - a[1])[0];
		const topDoctor = Object.entries(doctorCounts).sort((a, b) => b[1] - a[1])[0];
		const recentCases = items.value
			.slice(0, 3)
			.map(note => {
				const patient = note.patient_detail?.name || "a patient";
				return `${patient} treated for ${note.diagnosis || 'unspecified condition'}`;
			});

		const parts = [
			`There are ${total} treatment notes recorded.`,
			topDiagnosis ? `${topDiagnosis[0]} is the most common diagnosis with ${topDiagnosis[1]} cases.` : '',
			topDoctor ? `${topDoctor[0]} has authored the most notes at ${topDoctor[1]}.` : '',
			recentCases.length ? `Recent cases include ${recentCases.join(', ')}.` : ''
		];

		await speakInsights(parts);
	} catch (err) {
		console.error("Treatment notes voice insights failed", err);
		alert("Unable to generate treatment notes voice insights.");
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
	padding: 8px 14px;
	background: #3b82f6;
	color: #fff;
	border: none;
	border-radius: 6px;
	cursor: pointer;
}
.btn:disabled {
	opacity: 0.6;
	cursor: not-allowed;
}
</style>


