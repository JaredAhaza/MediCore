<template>
	<div class="card" style="max-width:520px;">
		<h3>New Prescription</h3>
		<form @submit.prevent="save">
			<label>Patient ID</label>
			<input v-model.number="form.patient" type="number" required />
			<label>Medication</label>
			<input v-model="form.medication" required />
			<label>Dosage</label>
			<input v-model="form.dosage" required />
			<label>Duration</label>
			<input v-model="form.duration" required />
			<label>Instructions</label>
			<textarea v-model="form.instructions" />
			<button :disabled="saving">{{ saving ? 'Saving...' : 'Create' }}</button>
			<p v-if="err" style="color:red; margin-top:.5rem;">{{ err }}</p>
		</form>
	</div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api/client";

const router = useRouter();
const form = reactive({ patient: null, medication: "", dosage: "", duration: "", instructions: "", status: "PENDING" });
const err = ref(""); const saving = ref(false);

async function save() {
	err.value = ""; saving.value = true;
	try {
		await api.post("/api/prescriptions/", form);
		router.push({ name: "PrescriptionsList" });
	} catch (e) {
		err.value = e?.response?.data ? JSON.stringify(e.response.data) : "Failed";
	} finally {
		saving.value = false;
	}
}
</script>


