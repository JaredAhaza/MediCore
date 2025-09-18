import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Landing from "../views/Landing.vue";
import Login from "../views/Login.vue";
import PatientsList from "../views/PatientsList.vue";
import PatientCreate from "../views/PatientCreate.vue";
import Me from "../views/Me.vue";

const routes = [
	{ path: "/", name: "Landing", component: Landing },
	{ path: "/login", name: "Login", component: Login },
	{ path: "/me", name: "Me", component: Me, meta: { auth: true } },
	{ path: "/patients", name: "PatientsList", component: PatientsList, meta: { auth: true } },
	{ path: "/patients/new", name: "PatientCreate", component: PatientCreate, meta: { auth: true, write: true } },
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
	return true;
});

export default router;
