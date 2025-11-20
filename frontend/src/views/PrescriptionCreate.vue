<template>
	<div class="card" style="max-width:640px;">
		<h3>New Prescription</h3>
		<form @submit.prevent="save">
			<SearchableSelect
				v-model="selectedPatient"
				label="Patient *"
				:fetcher="fetchPatients"
				:required="true"
				:disabled="patientFromQuery"
				placeholder="Type a name, username, medical ID or national ID"
				hint="Only active patients with usernames are listed"
			/>
			<small v-if="patientFromQuery" style="color:#666;">Patient pre-selected from list</small>

			<div v-if="selectedPatient" class="info-panel">
				<strong>{{ selectedPatient.label }}</strong>
				<div>{{ selectedPatient.subtitle }}</div>
				<div v-if="selectedPatient.meta" style="color:#636e72; font-size:0.85em;">
					{{ selectedPatient.meta }}
				</div>
			</div>

			<SearchableSelect
				v-model="selectedMedicine"
				label="Medication *"
				:fetcher="fetchMedicines"
				:required="true"
				placeholder="Search by item name, SKU or category"
				hint="Only in-stock and active medicines are shown"
			/>

			<div v-if="selectedMedicine" class="info-panel warning">
				<strong>{{ selectedMedicine.label }}</strong>
				<div>{{ selectedMedicine.subtitle }}</div>
				<div v-if="selectedMedicine.meta" style="color:#636e72; font-size:0.85em;">
					{{ selectedMedicine.meta }}
				</div>
			</div>

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
import { reactive, ref, computed, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import api from "../api/client";
import SearchableSelect from "@/components/SearchableSelect.vue";

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
const selectedPatient = ref(null);
const selectedMedicine = ref(null);

// Check if patient came from query param (from PatientsList)
const patientFromQuery = computed(() => !!route.query.patient_username);

watch(selectedPatient, (option) => {
	form.patient_username = option?.raw?.username || "";
});

watch(selectedMedicine, (option) => {
	form.medication = option?.raw?.name || "";
});

onMounted(async () => {
	// Auto-select patient if coming from patient list
	const username = route.query.patient_username;
	if (!username) return;

	const seeded = seedPatientFromRoute(route.query);
	if (seeded) {
		selectedPatient.value = mapPatientOption(seeded);
	}

	if (!selectedPatient.value) {
		await preloadPatientByUsername(username);
	}
});

async function save() {
	if (!selectedPatient.value) {
		err.value = "Please select a patient from the list.";
		return;
	}
	if (!selectedMedicine.value) {
		err.value = "Please select a medicine from inventory.";
		return;
	}

	err.value = "";
	saving.value = true;
	try {
		const payload = {
			patient_username: selectedPatient.value.raw?.username,
			medication: selectedMedicine.value.raw?.name,
			dosage: form.dosage,
			duration: form.duration,
			instructions: form.instructions,
			status: form.status,
		};
		await api.post("/api/prescriptions/", payload);
		router.push({ name: "PrescriptionsList" });
	} catch (e) {
		if (e?.response?.data) {
			err.value = formatApiError(e.response.data);
		} else {
			err.value = e?.message || "Failed to create prescription.";
		}
	} finally {
		saving.value = false;
	}
}

function mapPatientOption(patient) {
	return {
		id: patient.id,
		label: `${patient.name || "Unnamed"}${patient.username ? ` (${patient.username})` : ""}`,
		subtitle: [
			patient.medical_id ? `Medical ID: ${patient.medical_id}` : null,
			patient.national_id ? `National ID: ${patient.national_id}` : null,
		].filter(Boolean).join(" • "),
		meta: [
			patient.gender ? `Gender: ${patient.gender}` : null,
			patient.dob ? `DOB: ${patient.dob}` : null,
			patient.contact ? `Contact: ${patient.contact}` : null,
		].filter(Boolean).join(" • "),
		raw: patient,
	};
}

function mapMedicineOption(medicine) {
	return {
		id: medicine.id,
		label: medicine.name,
		subtitle: `Stock: ${medicine.current_stock ?? 0} • Kshs ${formatMoney(medicine.selling_price || 0)}`,
		meta: [
			medicine.category ? `Category: ${medicine.category}` : null,
			medicine.sku ? `SKU: ${medicine.sku}` : null,
		].filter(Boolean).join(" • "),
		raw: medicine,
	};
}

function formatMoney(value) {
	const num = Number(value || 0);
	return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function fetchPatients(search = "", cursor = null) {
	const params = { is_active: true };
	if (search) params.search = search;
	if (cursor) params.cursor = cursor;
	const { data } = await api.get("/api/patients/", { params });
	const { list, nextCursor } = normalizePaginated(data);
	const options = list.filter(p => p.username).map(mapPatientOption);
	return { items: options, nextCursor };
}

async function fetchMedicines(search = "", cursor = null) {
	const params = { is_active: true, in_stock: true };
	if (search) params.search = search;
	if (cursor) params.cursor = cursor;
	const { data } = await api.get("/api/pharmacy/medicines/", { params });
	const { list, nextCursor } = normalizePaginated(data);
	const options = list.filter(m => (m.current_stock ?? 0) > 0).map(mapMedicineOption);
	return { items: options, nextCursor };
}

function normalizePaginated(payload) {
	if (Array.isArray(payload)) {
		return { list: payload, nextCursor: null };
	}
	if (payload && Array.isArray(payload.results)) {
		return { list: payload.results, nextCursor: payload.next || payload.nextCursor || null };
	}
	if (payload && Array.isArray(payload.items)) {
		return { list: payload.items, nextCursor: payload.nextCursor || payload.next || null };
	}
	return { list: [], nextCursor: null };
}

async function preloadPatientByUsername(username) {
	try {
		const { data } = await api.get("/api/patients/", { params: { search: username } });
		const { list } = normalizePaginated(data);
		const match = list.find(p => p.username === username);
		if (match) {
			selectedPatient.value = mapPatientOption(match);
		}
	} catch (error) {
		console.warn("Failed to preload patient", error);
	}
}

function seedPatientFromRoute(query) {
	const username = query.patient_username;
	const name = query.patient_name;
	if (!username || !name) return null;
	return {
		id: query.patient_id ? Number(query.patient_id) : undefined,
		username,
		name,
		medical_id: query.patient_medical_id,
		national_id: query.patient_national_id,
		gender: query.patient_gender,
		dob: query.patient_dob,
		contact: query.patient_contact,
	};
}

function formatApiError(data) {
	if (typeof data === "string") return data;
	if (Array.isArray(data)) return data.join("; ");
	return Object.entries(data)
		.map(([key, value]) => {
			if (Array.isArray(value)) return `${key}: ${value.join(", ")}`;
			if (typeof value === "object" && value !== null) return `${key}: ${JSON.stringify(value)}`;
			return `${key}: ${value}`;
		})
		.join(" | ");
}
</script>

<style scoped>
.info-panel {
	margin: 0.5rem 0 1rem;
	padding: 12px;
	border-radius: 6px;
	background: #f7fbff;
	border-left: 4px solid #0984e3;
	font-size: 0.9em;
	line-height: 1.5;
}

.info-panel.warning {
	background: #fff8e6;
	border-left-color: #f39c12;
}
</style>