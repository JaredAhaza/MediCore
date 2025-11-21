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

			<!-- Prescription File Upload -->
			<div class="upload-section">
				<label>
					📄 Prescription File (Optional)
					<span class="help-text">Upload scanned prescription (Image or PDF)</span>
				</label>
				
				<div class="upload-area">
					<input 
						type="file" 
						id="prescription_image"
						ref="fileInput"
						@change="handleFileChange"
						accept="image/*,application/pdf"
						capture="environment"
						style="display: none;"
					/>
					
					<button 
						type="button" 
						@click="$refs.fileInput.click()"
						class="upload-btn"
					>
						<span v-if="!prescriptionImage">📷 Take Photo / Upload File</span>
						<span v-else>✓ Change File</span>
					</button>

					<div v-if="prescriptionImage" class="image-preview">
						<div v-if="isPDF" class="pdf-indicator">
							📄 PDF File
						</div>
						<img v-else :src="imagePreviewUrl" alt="Prescription preview" />
						<button 
							type="button" 
							@click="removeImage"
							class="remove-btn"
						>
							✕ Remove
						</button>
						<p class="file-name">{{ prescriptionImage.name }}</p>
					</div>
				</div>
			</div>

			<button :disabled="saving">{{ saving ? 'Saving...' : 'Create' }}</button>
			<p v-if="err" style="color:red; margin-top:.5rem;">{{ err }}</p>
		</form>
	</div>
</template>

<script setup>
import SearchableSelect from "@/components/SearchableSelect.vue";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
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
const selectedPatient = ref(null);
const selectedMedicine = ref(null);
const prescriptionImage = ref(null);
const imagePreviewUrl = ref(null);

// Check if patient came from query param (from PatientsList)
const patientFromQuery = computed(() => !!route.query.patient_username);

// Check if selected file is PDF
const isPDF = computed(() => {
	return prescriptionImage.value?.type === 'application/pdf';
});

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

function handleFileChange(event) {
	const file = event.target.files[0];
	if (file) {
		prescriptionImage.value = file;
		// Create preview URL only for images
		if (file.type.startsWith('image/')) {
			imagePreviewUrl.value = URL.createObjectURL(file);
		}
	}
}

function removeImage() {
	prescriptionImage.value = null;
	imagePreviewUrl.value = null;
	// Reset file input
	const fileInput = document.getElementById('prescription_image');
	if (fileInput) {
		fileInput.value = '';
	}
}

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
		// Use FormData for file upload
		const formData = new FormData();
		formData.append('patient_username', selectedPatient.value.raw?.username);
		formData.append('medication', selectedMedicine.value.raw?.name);
		formData.append('dosage', form.dosage);
		formData.append('duration', form.duration);
		formData.append('instructions', form.instructions);
		formData.append('status', form.status);
		
		// Add file if selected
		if (prescriptionImage.value) {
			formData.append('prescription_image', prescriptionImage.value);
		}

		await api.post("/api/prescriptions/", formData);
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

.upload-section {
	margin: 1.5rem 0;
}

.upload-section label {
	display: block;
	margin-bottom: 0.5rem;
	font-weight: 600;
}

.help-text {
	display: block;
	font-size: 0.85em;
	color: #7f8c8d;
	font-weight: normal;
	margin-top: 4px;
}

.upload-area {
	margin-top: 0.5rem;
}

.upload-btn {
	background: #3498db;
	color: white;
	padding: 12px 20px;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	font-size: 1em;
	font-weight: 600;
	transition: all 0.2s;
	display: inline-flex;
	align-items: center;
	gap: 8px;
}

.upload-btn:hover {
	background: #2980b9;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

.image-preview {
	margin-top: 1rem;
	padding: 15px;
	background: #f8f9fa;
	border-radius: 8px;
	border: 2px dashed #dee2e6;
}

.image-preview img {
	max-width: 100%;
	height: auto;
	border-radius: 6px;
	margin-bottom: 10px;
	box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.pdf-indicator {
	padding: 40px;
	text-align: center;
	font-size: 3em;
	background: #fff;
	border-radius: 6px;
	margin-bottom: 10px;
}

.remove-btn {
	background: #e74c3c;
	color: white;
	padding: 8px 16px;
	border: none;
	border-radius: 6px;
	cursor: pointer;
	font-size: 0.9em;
	font-weight: 600;
	transition: all 0.2s;
}

.remove-btn:hover {
	background: #c0392b;
}

.file-name {
	margin: 10px 0 0 0;
	font-size: 0.85em;
	color: #636e72;
	font-style: italic;
}
</style>