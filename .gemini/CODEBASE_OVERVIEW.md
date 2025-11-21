# MediCore - Complete Codebase Overview

**Generated**: November 20, 2025

## 📋 Project Summary

**MediCore** is a comprehensive clinic management system with a **Django REST Framework** backend and **Vue 3** frontend. It manages patients, prescriptions, pharmacy inventory, and financial operations for healthcare facilities.

---

## 🏗️ Architecture

### Technology Stack

#### Backend
- **Framework**: Django 5.2.6 + Django REST Framework 3.16.1
- **Authentication**: JWT (djangorestframework-simplejwt 5.5.1)
- **Database**: PostgreSQL (via Supabase pooler)
- **Server**: Gunicorn 21.2.0 with WhiteNoise for static files
- **Additional**: Google Generative AI integration, CORS support

#### Frontend
- **Framework**: Vue 3.5.21 (Composition API)
- **Build Tool**: Vite 7.0.6
- **State Management**: Pinia 2.3.1
- **Routing**: Vue Router 4.5.1
- **HTTP Client**: Axios 1.13.2

---

## 📁 Backend Structure

### Apps & Modules

#### 1. **users** - User Management
- **Model**: `User` (extends AbstractUser)
  - Roles: `ADMIN`, `DOCTOR`, `LAB_TECH`, `PHARMACIST`, `FINANCE`, `PATIENT`
- **Endpoints**:
  - `POST /api/token/` - Obtain JWT tokens
  - `POST /api/token/refresh/` - Refresh access token
  - `GET /api/auth/me/` - Get current user profile

#### 2. **patients** - Patient & Visit Management
- **Models**:
  - `Patient`: name, medical_id (unique), gender, dob, contact, address, user (OneToOne)
  - `Visit`: patient, doctor, date, reason, notes
  - `Prescription`: patient, doctor, medication, dosage, duration, instructions, status, pharmacist
- **Permissions**: `IsClinicianOrReadOnly` (read: all authenticated, write: ADMIN/DOCTOR/LAB_TECH/PHARMACIST)
- **Endpoints**:
  - `GET/POST /api/patients/`
  - `GET/PATCH/DELETE /api/patients/{id}/`
  - `GET/POST /api/visits/`
  - `GET/PATCH/DELETE /api/visits/{id}/`
- **Features**: Search & ordering on name, medical_id, contact

#### 3. **emr** - Electronic Medical Records
- **Models**:
  - `LabReport`: patient, lab_tech, report_type, results, status (PENDING/COMPLETED/REVIEWED)
  - `Prescription`: patient, doctor, medication, dosage, duration, instructions, status, pharmacist
  - `TreatmentNote`: patient, doctor, visit, diagnosis, treatment_plan, notes
- **Endpoints**:
  - `GET/POST /api/lab-reports/` (write: ADMIN/LAB_TECH)
  - `GET/POST/PATCH /api/prescriptions/` (create: ADMIN/DOCTOR; status update: PHARMACIST)
  - `GET/POST /api/treatment-notes/` (write: ADMIN/DOCTOR)

#### 4. **pharmacy** - Inventory & Dispensing
- **Models**:
  - `Medicine`: name, generic_name, category, manufacturer, current_stock, reorder_level, buying_price, selling_price
  - `InventoryTransaction`: medicine, transaction_type (STOCK_IN/STOCK_OUT/ADJUSTMENT/DISPENSED), quantity, batch_number, expiry_date
  - `Prescription`: patient, medication, dosage, duration, instructions, status
  - `PrescriptionDispense`: prescription (OneToOne), medicine, quantity_dispensed, pharmacist, amount_charged, discount_amount, additional_charges
- **Key Features**:
  - Stock management with atomic transactions
  - Low stock alerts & out-of-stock tracking
  - OCR invoice parsing for bulk stock-in
  - Profit/spend summaries
  - Finance overview (revenue, COGS, profit)
- **Endpoints**:
  - `GET/POST/PATCH/DELETE /api/pharmacy/medicines/`
  - `GET /api/pharmacy/medicines/low_stock/`
  - `GET /api/pharmacy/medicines/out_of_stock/`
  - `POST /api/pharmacy/medicines/{id}/add_stock/`
  - `GET /api/pharmacy/medicines/{id}/transaction_history/`
  - `GET/POST /api/pharmacy/inventory-transactions/`
  - `GET /api/pharmacy/inventory-transactions/profit_summary/`
  - `GET /api/pharmacy/inventory-transactions/spend_summary/`
  - `GET /api/pharmacy/inventory-transactions/finance_overview/`
  - `POST /api/pharmacy/inventory-transactions/stock_in/`
  - `POST /api/pharmacy/inventory-transactions/parse_invoice/`
  - `POST /api/pharmacy/inventory-transactions/apply_invoice/`
  - `GET/POST /api/pharmacy/dispenses/`

#### 5. **Finance** - Billing & Financial Tracking
- **Models**:
  - `Invoice`: patient, prescription, services (JSON), subtotal, discount, total, status (DUE/PAID/VOID)
  - `Payment`: invoice, recorded_by, amount, method (CASH/CARD/MPESA/INSURANCE), reference
  - `RevenueEntry`: occurred_on, category (INVOICE_PAYMENT/GRANT/OTHER), amount, invoice, recorded_by
  - `ExpenseEntry`: occurred_on, category (STOCK/OPERATIONS/SALARIES/OTHER), vendor, amount, recorded_by
- **Key Features**:
  - Auto-calculation of invoice totals
  - Payment tracking with multiple methods
  - Revenue & expense categorization
  - Financial position reports
  - CSV export for invoices
- **Endpoints**:
  - `GET/POST/PATCH/DELETE /api/invoices/`
  - `POST /api/invoices/{id}/void/`
  - `POST /api/invoices/create_for_prescription/`
  - `GET /api/invoices/{id}/download/`
  - `GET /api/invoices/download_all/`
  - `GET/POST /api/payments/`
  - `GET/POST /api/revenues/`
  - `GET/POST /api/expenses/`
  - `GET /api/finance/reports/financial-position/`

#### 6. **core** - Utilities & Management Commands
- **Management Commands**:
  - `test_db` - Database connectivity test
  - `test_users` - User roles test
  - `test_api` - API auth test
  - `test_patients` - Patients & visits CRUD test
  - `test_emr` - EMR functionality test
  - `test_finance` - Finance operations test
  - `run_all_tests` - Run all tests
  - `clean_test_data` - Clean test data
- **Features**: Idempotent tests with `--no-reset` option

---

## 🎨 Frontend Structure

### Directory Layout
```
frontend/src/
├── api/
│   └── client.js          # Axios instance with JWT interceptors
├── components/
│   ├── ExpensesPanel.vue
│   ├── FinanceSummary.vue
│   ├── InvoiceImport.vue
│   ├── NavBar.vue
│   └── SearchableSelect.vue
├── composables/
│   ├── useDraftForm.js
│   └── useVoiceInsights.js  # AI voice insights feature
├── router/
│   └── index.js           # Route definitions with role guards
├── stores/
│   └── auth.js            # Pinia auth store
├── views/
│   ├── Landing.vue
│   ├── Login.vue
│   ├── Me.vue
│   ├── PatientsList.vue
│   ├── PatientCreate.vue
│   ├── PrescriptionsList.vue
│   ├── PrescriptionCreate.vue
│   ├── TreatmentNotesList.vue
│   ├── TreatmentNoteCreate.vue
│   ├── PharmacyDashboard.vue
│   ├── MedicineList.vue
│   ├── MedicineForm.vue
│   ├── MedicineDetail.vue
│   ├── StockManagement.vue
│   ├── DispensePrescription.vue
│   ├── DispenseMedicineDetails.vue
│   ├── FinanceDashboard.vue
│   └── InvoicesList.vue
├── App.vue
└── main.js
```

### Key Routes

| Route | Component | Access |
|-------|-----------|--------|
| `/` | Landing | Public |
| `/login` | Login | Public |
| `/me` | Me | Authenticated |
| `/patients` | PatientsList | Authenticated |
| `/patients/new` | PatientCreate | Write role |
| `/emr/prescriptions` | PrescriptionsList | Authenticated |
| `/emr/prescriptions/new` | PrescriptionCreate | ADMIN/DOCTOR |
| `/emr/treatment-notes` | TreatmentNotesList | Authenticated |
| `/emr/treatment-notes/new` | TreatmentNoteCreate | ADMIN/DOCTOR |
| `/pharmacy` | PharmacyDashboard | Authenticated |
| `/pharmacy/medicines` | MedicineList | Authenticated |
| `/pharmacy/medicines/new` | MedicineForm | ADMIN/PHARMACIST |
| `/pharmacy/medicines/:id` | MedicineEdit | ADMIN/PHARMACIST |
| `/pharmacy/medicines/:id/details` | MedicineDetail | Authenticated |
| `/pharmacy/stock` | StockManagement | ADMIN/PHARMACIST |
| `/pharmacy/dispense` | DispensePrescription | ADMIN/PHARMACIST |
| `/pharmacy/dispense/:prescriptionId` | DispenseMedicineDetails | ADMIN/PHARMACIST |
| `/finance` | FinanceDashboard | ADMIN/FINANCE |
| `/finance/invoices` | InvoicesList | ADMIN/FINANCE |

### Authentication Flow

1. **Login**: User submits credentials → Backend returns JWT tokens → Stored in localStorage
2. **Request Interceptor**: Attaches `Authorization: Bearer <token>` to all requests
3. **Response Interceptor**: On 401, attempts token refresh → If fails, redirects to login
4. **Route Guards**: Check authentication & role before allowing navigation

### State Management (Pinia)

**Auth Store** (`stores/auth.js`):
- State: `user`, `access`, `refresh`, `loading`, `error`
- Actions:
  - `login(username, password)` - Authenticate user
  - `refreshToken()` - Refresh access token
  - `fetchMe()` - Get current user profile
  - `logout()` - Clear auth state
  - `hasWriteRole()` - Check if user can write data

---

## 🔐 Permissions & Roles

### Role Hierarchy
1. **ADMIN** - Full access to all features
2. **DOCTOR** - Patient records, prescriptions, treatment notes
3. **LAB_TECH** - Lab reports, patient records (read)
4. **PHARMACIST** - Pharmacy inventory, dispensing, prescription status updates
5. **FINANCE** - Invoices, payments, financial reports
6. **PATIENT** - Limited access (future feature)

### Permission Classes
- `IsClinicianOrReadOnly` - Read: all authenticated, Write: ADMIN/DOCTOR/LAB_TECH/PHARMACIST
- `IsPharmacyStaff` - ADMIN/PHARMACIST
- `CanDispensePrescription` - ADMIN/PHARMACIST
- `CanImportInvoices` - ADMIN/FINANCE
- `IsFinanceOrReadOnly` - Read: all authenticated, Write: ADMIN/FINANCE

---

## 🚀 Deployment

### Backend
- **Platform**: Render.com
- **Build**: `build.sh` script
- **Process**: Gunicorn WSGI server
- **Static Files**: WhiteNoise (serves Vue frontend in production)
- **Environment Variables**: `.env` file (not committed)
  - `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
  - `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_ALL_ORIGINS`, `CORS_ALLOWED_ORIGIN_REGEXES`
  - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

### Frontend
- **Platform**: Vercel
- **Build Command**: `npm run build`
- **Output**: `dist/` directory
- **Environment**: `.env.development` with `VITE_API_BASE`

---

## 🌟 Special Features

### 1. Voice Insights
- **Composable**: `useVoiceInsights.js`
- **Usage**: Pharmacy & Finance dashboards
- **Functionality**: AI-generated spoken summaries of key metrics using Web Speech API

### 2. OCR Invoice Processing
- **Service**: `pharmacy/ocr.py` with Google Generative AI
- **Workflow**: Upload invoice → OCR parsing → Review → Apply to inventory
- **Endpoints**: `/parse_invoice/`, `/apply_invoice/`

### 3. Draft Form Auto-save
- **Composable**: `useDraftForm.js`
- **Functionality**: Auto-saves form data to localStorage, restores on page load

### 4. Financial Reporting
- **Endpoint**: `/api/finance/reports/financial-position/`
- **Metrics**: Revenue, expenses, net position, cash collected, accounts receivable
- **Breakdown**: By category, with date filtering

### 5. Profit Analytics
- **Endpoint**: `/api/pharmacy/inventory-transactions/profit_summary/`
- **Calculation**: Revenue - COGS from dispensed items
- **Filters**: Date range, medicine, pharmacist

---

## 📊 Database Schema Highlights

### Key Relationships
- `User` ↔ `Patient` (OneToOne via `patient_profile`)
- `Patient` → `Visit` (ForeignKey)
- `Patient` → `Prescription` (ForeignKey)
- `Patient` → `Invoice` (ForeignKey)
- `Medicine` → `InventoryTransaction` (ForeignKey)
- `Prescription` ↔ `PrescriptionDispense` (OneToOne)
- `Invoice` → `Payment` (ForeignKey)
- `Invoice` → `RevenueEntry` (ForeignKey)

### Unique Constraints
- `Patient.medical_id` - Unique patient identifier
- `Medicine.name` - Unique medicine name
- `PrescriptionDispense.prescription` - One dispense per prescription

---

## 🧪 Testing

### Management Commands
All tests are idempotent (clean prior data unless `--no-reset` flag):
- `python manage.py test_db` - Database connectivity
- `python manage.py test_users` - User roles
- `python manage.py test_api` - JWT auth
- `python manage.py test_patients` - Patients & visits CRUD
- `python manage.py test_emr` - EMR functionality
- `python manage.py test_finance` - Finance operations
- `python manage.py run_all_tests` - All tests
- `python manage.py clean_test_data` - Clean test data

---

## 🔧 Development Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Create .env file with database credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
# Create .env.development with VITE_API_BASE
npm run dev
```

---

## 📝 API Documentation

### Authentication
```http
POST /api/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Authenticated Requests
```http
GET /api/patients/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Search & Filtering
- Patients: `?search=<term>` (searches name, medical_id, contact)
- Ordering: `?ordering=<field>` or `?ordering=-<field>` (descending)
- Pharmacy: `?category=<category>&is_active=true`
- Finance: `?start=YYYY-MM-DD&end=YYYY-MM-DD`

---

## 🎯 Next Steps (from README)
1. Audit logs and analytics
2. Async tasks (Celery)
3. Dockerization
4. Enhanced patient portal features

---

## 📦 Dependencies

### Backend (requirements.txt)
- Django 5.2.6
- djangorestframework 3.16.1
- djangorestframework-simplejwt 5.5.1
- psycopg2-binary 2.9.10
- django-cors-headers 4.8.0
- python-dotenv 1.1.1
- gunicorn 21.2.0
- whitenoise 6.6.0
- google-generativeai 0.8.3
- requests 2.32.3

### Frontend (package.json)
- vue 3.5.21
- vue-router 4.5.1
- pinia 2.3.1
- axios 1.13.2
- vite 7.0.6
- @vitejs/plugin-vue 6.0.1

---

## 🏁 Summary

MediCore is a **production-ready clinic management system** with:
- ✅ Comprehensive patient & EMR management
- ✅ Advanced pharmacy inventory with OCR invoice processing
- ✅ Financial tracking with detailed reporting
- ✅ Role-based access control
- ✅ JWT authentication with auto-refresh
- ✅ Modern Vue 3 frontend with Pinia state management
- ✅ AI-powered voice insights
- ✅ PostgreSQL database with Supabase
- ✅ Deployed on Render (backend) & Vercel (frontend)

The codebase is well-structured, follows Django/Vue best practices, and includes comprehensive testing utilities.
