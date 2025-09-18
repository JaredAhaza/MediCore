import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Landing from "../views/Landing.vue";
import Login from "../views/Login.vue";
import PatientsList from "../views/PatientsList.vue";
import PatientCreate from "../views/PatientCreate.vue";
import Me from "../views/Me.vue";
import PrescriptionsList from "../views/PrescriptionsList.vue";
import PrescriptionCreate from "../views/PrescriptionCreate.vue";
import TreatmentNotesList from "../views/TreatmentNotesList.vue";
import TreatmentNoteCreate from "../views/TreatmentNoteCreate.vue";

const routes = [
	{ path: "/", name: "Landing", component: Landing },
	{ path: "/login", name: "Login", component: Login },
	{ path: "/me", name: "Me", component: Me, meta: { auth: true } },
	{ path: "/patients", name: "PatientsList", component: PatientsList, meta: { auth: true } },
	{ path: "/patients/new", name: "PatientCreate", component: PatientCreate, meta: { auth: true, write: true } },
    { path: "/emr/prescriptions", name: "PrescriptionsList", component: PrescriptionsList, meta: { auth: true } },
    { path: "/emr/prescriptions/new", name: "PrescriptionCreate", component: PrescriptionCreate, meta: { auth: true, role: ["ADMIN","DOCTOR"] } },
    { path: "/emr/treatment-notes", name: "TreatmentNotesList", component: TreatmentNotesList, meta: { auth: true } },
    { path: "/emr/treatment-notes/new", name: "TreatmentNoteCreate", component: TreatmentNoteCreate, meta: { auth: true, role: ["ADMIN","DOCTOR"] } },
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

router.beforeEach(async (to) => {
	const auth = useAuthStore();
	if (!auth.user && auth.access) {
		await auth.fetchMe().catch(() => {});
	}
	if (to.meta?.auth && !auth.access) return { name: "Login", query: { next: to.fullPath } };
    if (to.meta?.write && !auth.hasWriteRole()) return { name: "PatientsList" };
    if (to.meta?.role) {
        const r = auth.user?.role;
        if (!to.meta.role.includes(r)) return { name: "Landing" };
    }
	return true;
});

export default router;
