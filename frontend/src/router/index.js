import MedicineDetail from "@/views/MedicineDetail.vue";
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AdminDashboard from "../views/AdminDashboard.vue";
import DispenseMedicineDetails from "../views/DispenseMedicineDetails.vue";
import DispensePrescription from "../views/DispensePrescription.vue";
import FinanceDashboard from "../views/FinanceDashboard.vue";
import InvoicesList from "../views/InvoicesList.vue";
import Landing from "../views/Landing.vue";
import Login from "../views/Login.vue";
import Me from "../views/Me.vue";
import MedicineForm from "../views/MedicineForm.vue";
import MedicineList from "../views/MedicineList.vue";
import PatientCreate from "../views/PatientCreate.vue";
import PatientsList from "../views/PatientsList.vue";
import PharmacistDashboard from "../views/PharmacistDashboard.vue";
import PharmacyDashboard from "../views/PharmacyDashboard.vue";
import PrescriptionCreate from "../views/PrescriptionCreate.vue";
import PrescriptionsList from "../views/PrescriptionsList.vue";
import StockManagement from "../views/StockManagement.vue";
import TreatmentNoteCreate from "../views/TreatmentNoteCreate.vue";
import TreatmentNotesList from "../views/TreatmentNotesList.vue";
import UserCreate from "../views/UserCreate.vue";
import UsersList from "../views/UsersList.vue";

const routes = [
    { path: "/", name: "Landing", component: Landing },
    { path: "/login", name: "Login", component: Login },
    {
        path: "/dashboard", name: "Dashboard", redirect: (to) => {
            const auth = useAuthStore();
            const role = auth.user?.role;
            if (role === 'ADMIN') return '/admin/dashboard';
            if (role === 'PHARMACIST') return '/pharmacist/dashboard';
            if (role === 'DOCTOR') return '/patients';
            if (role === 'FINANCE') return '/finance';
            return '/me';
        }
    },

    // Admin Routes
    { path: "/admin/dashboard", name: "AdminDashboard", component: AdminDashboard, meta: { auth: true, role: ["ADMIN"] } },
    { path: "/admin/users", name: "UsersList", component: UsersList, meta: { auth: true, role: ["ADMIN"] } },
    { path: "/admin/users/new", name: "UserCreate", component: UserCreate, meta: { auth: true, role: ["ADMIN"] } },

    // Pharmacist Routes
    { path: "/pharmacist/dashboard", name: "PharmacistDashboard", component: PharmacistDashboard, meta: { auth: true, role: ["ADMIN", "PHARMACIST"] } },

    // General Routes
    { path: "/me", name: "Me", component: Me, meta: { auth: true } },
    { path: "/patients", name: "PatientsList", component: PatientsList, meta: { auth: true } },
    { path: "/patients/new", name: "PatientCreate", component: PatientCreate, meta: { auth: true, write: true } },
    { path: "/emr/prescriptions", name: "PrescriptionsList", component: PrescriptionsList, meta: { auth: true } },
    { path: "/emr/prescriptions/new", name: "PrescriptionCreate", component: PrescriptionCreate, meta: { auth: true, role: ["ADMIN", "DOCTOR", "PHARMACIST"] } },
    { path: "/emr/treatment-notes", name: "TreatmentNotesList", component: TreatmentNotesList, meta: { auth: true } },
    { path: "/emr/treatment-notes/new", name: "TreatmentNoteCreate", component: TreatmentNoteCreate, meta: { auth: true, role: ["ADMIN", "DOCTOR"] } },
    { path: "/pharmacy", name: "PharmacyDashboard", component: PharmacyDashboard, meta: { auth: true } },
    { path: "/pharmacy/medicines", name: "MedicineList", component: MedicineList, meta: { auth: true } },
    { path: "/pharmacy/medicines/new", name: "MedicineForm", component: MedicineForm, meta: { auth: true, role: ["ADMIN", "PHARMACIST"] } },
    { path: "/pharmacy/medicines/:id", name: "MedicineEdit", component: MedicineForm, meta: { auth: true, role: ["ADMIN", "PHARMACIST"] } },
    { path: "/pharmacy/stock", name: "StockManagement", component: StockManagement, meta: { auth: true, role: ["ADMIN", "PHARMACIST"] } },
    { path: "/pharmacy/dispense", name: "DispensePrescription", component: DispensePrescription, meta: { auth: true, role: ["ADMIN", "PHARMACIST"] } },
    { path: "/pharmacy/dispense/:prescriptionId", name: "DispenseMedicineDetails", component: DispenseMedicineDetails, meta: { auth: true, role: ["ADMIN", "PHARMACIST"] } },
    { path: "/pharmacy/medicines/:id/details", name: "MedicineDetail", component: MedicineDetail, meta: { auth: true } },
    { path: "/finance", name: "FinanceDashboard", component: FinanceDashboard, meta: { auth: true, role: ["ADMIN", "FINANCE", "PHARMACIST"] } },
    { path: "/finance/invoices", name: "InvoicesList", component: InvoicesList, meta: { auth: true, role: ["ADMIN", "FINANCE", "PHARMACIST"] } },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

router.beforeEach(async (to) => {
    const auth = useAuthStore();

    if (!auth.access && localStorage.getItem("refresh")) {
        await auth.refreshToken().catch(() => { });
    }

    if (!auth.user && auth.access) {
        await auth.fetchMe().catch(() => { });
    }

    if (to.meta?.auth && !auth.access) return { name: "Login", query: { next: to.fullPath } };
    if (to.meta?.write && !auth.hasWriteRole()) return { name: "PatientsList" };
    if (to.meta?.role) {
        const r = auth.user?.role;
        if (!to.meta.role.includes(r)) {
            // Redirect to appropriate dashboard if user doesn't have access
            if (r === 'ADMIN') return { name: "AdminDashboard" };
            if (r === 'PHARMACIST') return { name: "PharmacistDashboard" };
            return { name: "Landing" };
        }
    }
    return true;
});

export default router;
