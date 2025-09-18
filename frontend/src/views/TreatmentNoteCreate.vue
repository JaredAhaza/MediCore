<template>
	<div class="card" style="max-width:520px;">
		<h3>New Treatment Note</h3>
		<form @submit.prevent="save">
			<label>Patient ID</label>
			<input v-model.number="form.patient" type="number" required />
			<label>Visit ID (optional)</label>
			<input v-model.number="form.visit" type="number" />
			<label>Diagnosis</label>
			<input v-model="form.diagnosis" required />
			<label>Treatment Plan</label>
			<textarea v-model="form.treatment_plan" required />
			<label>Notes</label>
			<textarea v-model="form.notes" />
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
const form = reactive({ patient: null, visit: null, diagnosis: "", treatment_plan: "", notes: "" });
const err = ref(""); const saving = ref(false);

async function save() {
	err.value = ""; saving.value = true;
	try {
		await api.post("/api/treatment-notes/", form);
		router.push({ name: "TreatmentNotesList" });
	} catch (e) {
		err.value = e?.response?.data ? JSON.stringify(e.response.data) : "Failed";
	} finally {
		saving.value = false;
	}
}
</script>


