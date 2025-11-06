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
import PharmacyDashboard from "../views/PharmacyDashboard.vue";
import MedicineList from "../views/MedicineList.vue";
import MedicineForm from "../views/MedicineForm.vue";
import MedicineDetail from "@/views/MedicineDetail.vue";
import StockManagement from "../views/StockManagement.vue";
import DispensePrescription from "../views/DispensePrescription.vue";

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
    { path: "/pharmacy", name: "PharmacyDashboard", component: PharmacyDashboard, meta: { auth: true } },
    { path: "/pharmacy/medicines", name: "MedicineList", component: MedicineList, meta: { auth: true } },
    { path: "/pharmacy/medicines/new", name: "MedicineForm", component: MedicineForm, meta: { auth: true, role: ["ADMIN","PHARMACIST"] } },
    { path: "/pharmacy/medicines/:id", name: "MedicineEdit", component: MedicineForm, meta: { auth: true, role: ["ADMIN","PHARMACIST"] } },
    { path: "/pharmacy/stock", name: "StockManagement", component: StockManagement, meta: { auth: true, role: ["ADMIN","PHARMACIST"] } },
    { path: "/pharmacy/dispense", name: "DispensePrescription", component: DispensePrescription, meta: { auth: true, role: ["ADMIN","PHARMACIST"] } },
    { path: "/pharmacy/medicines/:id/details", name: "MedicineDetail", component: MedicineDetail, meta: { auth: true } },
];

const router = createRouter({
        history: createWebHistory(),
        routes,
});

router.beforeEach(async (to) => {
    const auth = useAuthStore();
  
    if (!auth.access && localStorage.getItem("refresh")) {
      await auth.refreshToken().catch(() => {});
    }
  
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
