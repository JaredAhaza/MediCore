<template>
	<div>
		<div class="card">
			<h3>Prescriptions</h3>
			<input v-model="q" placeholder="Search by patient or medication" @input="debouncedLoad" />
			<RouterLink v-if="canCreate" to="/emr/prescriptions/new">New Prescription</RouterLink>
		</div>
		<div v-for="p in items" :key="p.id" class="card">
			<b>{{ p.patient_detail?.name }}</b> — {{ p.medication }}
			<div style="font-size:.9em; color:#666;">Status: {{ p.status }} • Doctor: {{ p.doctor }}</div>
			<div v-if="canDispense">
				<select v-model="statuses[p.id]">
					<option>PENDING</option>
					<option>DISPENSED</option>
					<option>COMPLETED</option>
				</select>
				<button @click="updateStatus(p.id)">Update</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { useAuthStore } from "../stores/auth";
import { RouterLink } from "vue-router";
import api from "../api/client";

const auth = useAuthStore();
const q = ref("");
const items = ref([]);
const statuses = ref({});

const canCreate = ["ADMIN","DOCTOR"].includes(auth.user?.role);
const canDispense = ["ADMIN","PHARMACIST","DOCTOR"].includes(auth.user?.role);

async function load() {
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/prescriptions/", { params });
	items.value = data;
	for (const p of data) statuses.value[p.id] = p.status;
}

let timer;
function debouncedLoad() { clearTimeout(timer); timer = setTimeout(load, 250); }

async function updateStatus(id) {
	try {
		await api.patch(`/api/prescriptions/${id}/`, { status: statuses.value[id] });
		await load();
	} catch (e) {
		alert("Failed to update status");
	}
}

load();
</script>


