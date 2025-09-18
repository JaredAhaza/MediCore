<template>
	<div>
		<div class="card">
			<h3>Treatment Notes</h3>
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

const auth = useAuthStore();
const q = ref("");
const items = ref([]);
const canCreate = ["ADMIN","DOCTOR"].includes(auth.user?.role);

async function load() {
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/treatment-notes/", { params });
	items.value = data;
}

let timer;
function debouncedLoad() { clearTimeout(timer); timer = setTimeout(load, 250); }

load();
</script>


