<template>
	<div class="card" style="max-width:520px;">
		<h3>New Patient</h3>
		<form @submit.prevent="save">
			<label>Name</label>
			<input v-model="form.name" required />
			<label>DOB</label>
			<input v-model="form.dob" type="date" />
			<label>Gender</label>
			<select v-model="form.gender">
				<option value="">--</option>
				<option value="MALE">Male</option>
				<option value="FEMALE">Female</option>
				<option value="OTHER">Other</option>
			</select>
			<label>Contact</label>
			<input v-model="form.contact" />
			<label>Medical ID</label>
			<input v-model="form.medical_id" required />
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
const form = reactive({ name:"", dob:"", gender:"", contact:"", medical_id:"" });
const err = ref(""); const saving = ref(false);

async function save() {
	err.value = ""; saving.value = true;
	try {
		await api.post("/api/patients/", form);
		router.push({ name: "PatientsList" });
	} catch (e) {
		err.value = e?.response?.data ? JSON.stringify(e.response.data) : "Failed";
	} finally {
		saving.value = false;
	}
}
</script>
