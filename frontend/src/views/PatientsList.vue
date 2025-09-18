<template>
	<div>
		<div class="card">
			<h3>Patients</h3>
			<input v-model="q" placeholder="Search by name or medical ID" @input="debouncedLoad" />
		</div>
		<div v-for="p in patients" :key="p.id" class="card">
			<b>{{ p.name }}</b> — {{ p.medical_id }}
			<div style="font-size:.9em; color:#666;">{{ p.gender }} • {{ p.dob }}</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import api from "../api/client";
let timer;
const q = ref("");
const patients = ref([]);

async function load() {
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/patients/", { params });
	patients.value = data;
}
function debouncedLoad() {
	clearTimeout(timer);
	timer = setTimeout(load, 250);
}
load();
</script>
