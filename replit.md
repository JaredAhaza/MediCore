# MediCore - Clinic Management System

## Project Overview
MediCore is a comprehensive clinic management system built with Django REST Framework (backend) and Vue 3 (frontend). The system manages patient records, visits, prescriptions, treatment notes, lab reports, and financial operations for healthcare facilities.

**Last Updated:** October 31, 2025

## Current State
✅ **Fully configured and running in Replit environment**
- Backend (Django 5 + DRF) running on port 8000
- Frontend (Vue 3 + Vite) running on port 5000
- SQLite database initialized with migrations applied
- Both workflows configured and operational
- Deployment configuration ready for production

## Project Architecture

### Backend (Django)
**Location:** `backend/`
**Port:** 8000
**Framework:** Django 5.2.6 + Django REST Framework

**Apps:**
- `users` - Custom user model with role-based access (ADMIN, DOCTOR, LAB_TECH, PHARMACIST, FINANCE, PATIENT)
- `patients` - Patient records and visit management
- `emr` - Electronic Medical Records (prescriptions, treatment notes, lab reports)
- `Finance` - Invoicing and payment management
- `core` - Management commands and shared utilities

**Authentication:** JWT-based authentication using SimpleJWT

**Database:** SQLite (development), supports PostgreSQL (production)

**Key Environment Variables:**
```
DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=*
USE_SQLITE=1
CORS_ALLOW_ALL_ORIGINS=1
```

### Frontend (Vue)
**Location:** `frontend/`
**Port:** 5000
**Framework:** Vue 3 + Vite

**Features:**
- Vue Router for navigation
- Pinia for state management
- Axios for API communication
- Role-based route guards
- JWT authentication with automatic token refresh

**API Base URL:** `https://[replit-domain]:8000`

### Key API Endpoints
- `POST /api/token/` - Obtain JWT tokens
- `POST /api/token/refresh/` - Refresh access token
- `GET /api/auth/me/` - Get current user profile
- `/api/patients/` - Patient CRUD operations
- `/api/visits/` - Visit management
- `/api/prescriptions/` - Prescription management
- `/api/treatment-notes/` - Treatment notes
- `/api/lab-reports/` - Lab report management

## Development Setup

### Prerequisites
- Python 3.11
- Node.js 20+

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Default Admin User
- **Username:** admin
- **Email:** admin@medicore.com
- **Password:** (set during createsuperuser)

## Workflows

### frontend
- **Command:** `cd frontend && npm run dev`
- **Port:** 5000
- **Output:** webview
- **Purpose:** Serves the Vue application with hot module replacement

### backend
- **Command:** `cd backend && python manage.py runserver 0.0.0.0:8000`
- **Port:** 8000
- **Output:** console
- **Purpose:** Runs Django development server for API

## Deployment

### Configuration
The project is configured for Replit Autoscale deployment:

**Build Process:**
1. Install frontend dependencies
2. Build Vue production assets
3. Install backend dependencies
4. Collect static files
5. Run database migrations

**Run Command:**
- Gunicorn WSGI server on port 5000
- Serves both API and static frontend files

### Production Checklist
- [ ] Update `SECRET_KEY` in production environment
- [ ] Set `DEBUG=0` in production
- [ ] Configure PostgreSQL database if needed
- [ ] Set up proper domain and CORS settings
- [ ] Configure proper `ALLOWED_HOSTS`

## Database

### Current Setup
- **Type:** SQLite (db.sqlite3)
- **Migrations:** All applied
- **Superuser:** Created (admin)

### PostgreSQL Migration (Optional)
To switch to PostgreSQL:
1. Create a PostgreSQL database in Replit
2. Set environment variables:
   ```
   USE_SQLITE=0
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=your_db_host
   DB_PORT=5432
   ```
3. Run migrations: `python manage.py migrate`

## Management Commands

The project includes custom management commands for testing:

```bash
# Test database connectivity
python manage.py test_db

# Test user roles and authentication
python manage.py test_users

# Test JWT API authentication
python manage.py test_api

# Test patient CRUD operations
python manage.py test_patients

# Test EMR functionality
python manage.py test_emr

# Run all tests
python manage.py run_all_tests

# Clean test data
python manage.py clean_test_data
```

## Role-Based Permissions

**Read Access (All Authenticated Users):**
- View patients, visits, prescriptions, treatment notes, lab reports

**Write Access by Role:**
- **ADMIN:** Full access to all resources
- **DOCTOR:** Create/edit patients, visits, prescriptions, treatment notes
- **LAB_TECH:** Create/edit patients, lab reports
- **PHARMACIST:** Update prescription status, view all records
- **FINANCE:** Manage invoices and payments

## File Structure
```
.
├── backend/
│   ├── Medicore/          # Django project settings
│   ├── users/             # User authentication app
│   ├── patients/          # Patient management app
│   ├── emr/               # Electronic medical records app
│   ├── Finance/           # Finance management app
│   ├── core/              # Core utilities and commands
│   ├── manage.py
│   ├── requirements.txt
│   └── .env              # Environment variables (not in git)
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # Vue components
│   │   ├── router/       # Vue Router config
│   │   ├── stores/       # Pinia stores
│   │   ├── views/        # Page components
│   │   ├── App.vue
│   │   └── main.js
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── .env.development
├── .gitignore
└── replit.md            # This file
```

## Recent Changes
- **2025-10-31:** Initial Replit environment setup
  - Configured Django settings for Replit environment
  - Added SQLite/PostgreSQL database switching
  - Configured Vite to bind to 0.0.0.0:5000 with host allowlist
  - Updated frontend API base URL to use Replit domain
  - Set up workflows for both frontend and backend
  - Configured deployment settings for production
  - Applied all database migrations
  - Created admin superuser

## User Preferences
- Using SQLite for development (easy setup, no external dependencies)
- Following existing project structure and conventions
- Maintaining separation between frontend and backend
- Using environment variables for configuration

## Next Steps / Roadmap
1. **Finance Module Enhancement**
   - Complete invoice and payment functionality
   - Add financial reports and analytics

2. **Advanced Features**
   - Implement audit logs for all operations
   - Add analytics dashboard
   - Set up async tasks with Celery
   - Add email notifications

3. **Production Readiness**
   - Comprehensive testing suite
   - API documentation (OpenAPI/Swagger)
   - Performance optimization
   - Security hardening

## Troubleshooting

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check CORS settings in backend/.env
- Ensure VITE_API_BASE in frontend/.env.development is correct

### Database errors
- Run `python manage.py migrate` to apply migrations
- Check if db.sqlite3 file exists in backend/
- Verify database permissions

### Port conflicts
- Ensure no other services are using ports 5000 or 8000
- Restart workflows if needed

## Support & Resources
- Django Documentation: https://docs.djangoproject.com/
- Vue 3 Documentation: https://vuejs.org/
- DRF Documentation: https://www.django-rest-framework.org/
- Vite Documentation: https://vitejs.dev/
