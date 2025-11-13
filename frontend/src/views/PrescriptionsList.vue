<template>
	<div>
		<div class="card">
			<h3>Prescriptions</h3>
			<input
				v-model="q"
				placeholder="Search by patient or medication"
				@input="debouncedLoad"
			/>
			<RouterLink v-if="canCreate" to="/emr/prescriptions/new">
				New Prescription
			</RouterLink>
		</div>

		<!-- Pending Prescriptions -->
		<div v-if="pendingPrescriptions.length">
			<h4>Pending Prescriptions</h4>
			<div
				v-for="p in pendingPrescriptions"
				:key="p.id"
				class="card"
				style="border-left: 4px solid #f39c12;"
			>
				<b>{{ p.patient_detail?.name }}</b> — {{ p.medication }}
				<div style="font-size:.9em; color:#666;">
					Status: <span class="badge pending">{{ p.status }}</span>
					• Doctor: {{ p.doctor }}
				</div>

				<div v-if="canDispense">
					<RouterLink
						:to="{ name: 'DispenseMedicineDetails', params: { prescriptionId: p.id } }"
						class="btn"
					>
						Dispense
					</RouterLink>
				</div>
			</div>
		</div>

		<!-- Dispensed Prescriptions -->
		<div v-if="dispensedPrescriptions.length">
			<h4>Dispensed Prescriptions</h4>
			<div
				v-for="p in dispensedPrescriptions"
				:key="p.id"
				class="card locked"
				style="border-left: 4px solid #27ae60;"
			>
				<b>{{ p.patient_detail?.name }}</b> — {{ p.medication }}
				<div style="font-size:.9em; color:#666;">
					Status: <span class="badge dispensed">DISPENSED</span> • Doctor: {{ p.doctor }}
				</div>
				<small style="color:#999;">Prescription completed — status locked.</small>
			</div>
		</div>

		<!-- Cancelled Prescriptions -->
		<div v-if="cancelledPrescriptions.length">
			<h4>Cancelled Prescriptions</h4>
			<div
				v-for="p in cancelledPrescriptions"
				:key="p.id"
				class="card"
				style="border-left: 4px solid #e74c3c;"
			>
				<b>{{ p.patient_detail?.name }}</b> — {{ p.medication }}
				<div style="font-size:.9em; color:#666;">
					Status: <span class="badge cancelled">CANCELLED</span> • Doctor: {{ p.doctor }}
				</div>
				<button @click="reinstatePrescription(p.id)">Re-initiate</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { RouterLink } from "vue-router";
import api from "../api/client";

const auth = useAuthStore();
const route = useRoute();
const q = ref("");
const items = ref([]);

const canCreate = ["ADMIN", "DOCTOR"].includes(auth.user?.role);
const canDispense = ["ADMIN", "PHARMACIST", "DOCTOR"].includes(auth.user?.role);

const pendingPrescriptions = computed(() =>
	items.value.filter((p) => p.status === "PENDING")
);
const dispensedPrescriptions = computed(() =>
	items.value.filter((p) => p.status === "DISPENSED")
);
const cancelledPrescriptions = computed(() =>
	items.value.filter((p) => p.status === "CANCELLED")
);

async function load() {
	const params = {};
	if (q.value) params.search = q.value;
	const { data } = await api.get("/api/prescriptions/", { params });
	items.value = data;
}

let timer;
function debouncedLoad() {
	clearTimeout(timer);
	timer = setTimeout(load, 250);
}


async function reinstatePrescription(id) {
	try {
		await api.patch(`/api/prescriptions/${id}/`, { status: "PENDING" });
		await load();
	} catch (e) {
		alert("Failed to re-initiate prescription");
	}
}

// Seed the search box from patient query (coming from PatientsList "View Prescription")
if (route.query && route.query.patient) {
    q.value = String(route.query.patient);
}

load();
</script>

<style scoped>
.card {
	margin-bottom: 1rem;
	padding: 1rem;
	border: 1px solid #ddd;
	border-radius: 8px;
	background: #fff;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.locked {
	opacity: 0.8;
	pointer-events: none;
}
.badge {
	padding: 0.2em 0.5em;
	border-radius: 4px;
	font-weight: bold;
	color: #fff;
}
.badge.pending { background: #f39c12; }
.badge.dispensed { background: #27ae60; }
.badge.cancelled { background: #e74c3c; }
</style>
