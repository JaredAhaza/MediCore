<template>
	<div class="card" style="max-width:520px;">
		<h3>New Prescription</h3>
		<form @submit.prevent="save">
			<label>Patient *</label>
			<select v-model="form.patient_username" required :disabled="patientFromQuery">
				<option value="">Select Patient</option>
				<option v-for="patient in patients" :key="patient.id" :value="patient.username">
					{{ patient.name }} ({{ patient.username }})
				</option>
			</select>
			<small v-if="patientFromQuery" style="color:#666;">Patient pre-selected from list</small>

			<label>Medication *</label>
			<select v-model="form.medication" required>
				<option value="">Select Medication</option>
				<option v-for="med in inStockMedicines" :key="med.id" :value="med.name">
					{{ med.name }} (Stock: {{ med.current_stock }})
				</option>
			</select>

			<label>Dosage *</label>
			<input v-model="form.dosage" required placeholder="e.g. 1 tablet twice daily" />

			<label>Duration *</label>
			<input v-model="form.duration" required placeholder="e.g. 7 days" />

			<label>Instructions</label>
			<textarea v-model="form.instructions" placeholder="Optional instructions" />

			<button :disabled="saving">{{ saving ? 'Saving...' : 'Create' }}</button>
			<p v-if="err" style="color:red; margin-top:.5rem;">{{ err }}</p>
		</form>
	</div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import api from "../api/client";

const router = useRouter();
const route = useRoute();

const form = reactive({
	patient_username: "",
	medication: "",
	dosage: "",
	duration: "",
	instructions: "",
	status: "PENDING",
});

const err = ref("");
const saving = ref(false);
const patients = ref([]);
const medicines = ref([]);

// Check if patient came from query param (from PatientsList)
const patientFromQuery = computed(() => !!route.query.patient_username);

// Filter to only medicines with stock > 0
const inStockMedicines = computed(() => 
	medicines.value.filter(m => m.current_stock > 0 && m.is_active)
);

onMounted(async () => {
	// Auto-select patient if coming from patient list
	if (route.query.patient_username) {
		form.patient_username = route.query.patient_username;
	}

	// Load patients for dropdown
	try {
		const { data } = await api.get("/api/patients/");
		patients.value = data.filter(p => p.username); // only patients with usernames
	} catch (e) {
		console.error("Failed to load patients:", e);
	}

	// Load medicines (will filter to in-stock)
	try {
		const { data } = await api.get("/api/pharmacy/medicines/", { params: { is_active: true } });
		medicines.value = data;
	} catch (e) {
		console.error("Failed to load medicines:", e);
	}
});

async function save() {
	err.value = "";
	saving.value = true;
	try {
		// Send patient_username instead of patient ID (backend resolves it)
		const payload = {
			patient_username: form.patient_username,
			medication: form.medication,
			dosage: form.dosage,
			duration: form.duration,
			instructions: form.instructions,
			status: form.status,
		};
		await api.post("/api/prescriptions/", payload);
		router.push({ name: "PrescriptionsList" });
	} catch (e) {
		err.value = e?.response?.data ? JSON.stringify(e.response.data) : "Failed";
	} finally {
		saving.value = false;
	}
}
</script>