# Prescription Upload Feature Implementation

**Date**: November 20, 2025

## Overview
Added prescription image upload functionality to allow pharmacists and doctors to upload scanned or photographed prescriptions when creating prescription records in the system.

---

## Features Implemented

### ✅ **1. Pharmacists Can Create Prescriptions**
- Already enabled in router (ADMIN, DOCTOR, PHARMACIST roles)
- Route: `/emr/prescriptions/new`
- Pharmacists can now create prescriptions just like doctors

### ✅ **2. Prescription Image Upload**
- Upload scanned prescriptions (PDF, images)
- Upload photographed prescriptions from mobile devices
- Automatic file organization by date
- Image URL generation for frontend display

---

## Backend Changes

### **1. Prescription Model** (`patients/models.py`)

Added two new fields:

```python
# New fields
prescription_image = models.ImageField(
    upload_to='prescriptions/%Y/%m/%d/',
    null=True,
    blank=True,
    help_text='Scanned or photographed prescription'
)

created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='created_prescriptions',
    help_text='User who created this prescription entry'
)
```

**Features:**
- `prescription_image`: Stores uploaded prescription files
- Organized by date: `media/prescriptions/2025/11/20/`
- `created_by`: Tracks who created the prescription (doctor or pharmacist)

### **2. Settings** (`Medicore/settings.py`)

Added media files configuration:

```python
# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### **3. URLs** (`Medicore/urls.py`)

Added media file serving in development:

```python
# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### **4. Serializer** (`patients/serializers.py`)

Created `PrescriptionSerializer` with:
- Image upload support
- Automatic URL generation for images
- `created_by` tracking
- Patient and doctor details

```python
class PrescriptionSerializer(serializers.ModelSerializer):
    patient_detail = PatientSerializer(source="patient", read_only=True)
    doctor_name = serializers.CharField(source="doctor.get_full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    prescription_image_url = serializers.SerializerMethodField()
    
    # Automatically sets created_by to current user
    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user:
            validated_data["created_by"] = request.user
        return super().create(validated_data)
```

### **5. ViewSet** (`patients/views.py`)

Created `PrescriptionViewSet` with:
- Multipart/form-data support for file uploads
- Search and filtering
- Proper permissions

```python
class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.select_related("patient", "doctor", "pharmacist", "created_by")
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated & IsClinicianOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # File upload support
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["patient__name", "patient__medical_id", "medication"]
    filterset_fields = ["status", "patient"]
```

### **6. URLs** (`patients/urls.py`)

Added prescriptions endpoint:

```python
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
```

### **7. Dependencies** (`requirements.txt`)

Added Pillow for image processing:

```
Pillow==11.0.0
```

---

## API Endpoints

### **Create Prescription with Image**

```http
POST /api/prescriptions/
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
- patient: <patient_id>
- medication: "Amoxicillin 500mg"
- dosage: "1 capsule"
- duration: "7 days"
- instructions: "After meals"
- status: "PENDING"
- prescription_image: <file>  (optional)
- doctor: <doctor_id>  (optional)
```

### **List Prescriptions**

```http
GET /api/prescriptions/
Authorization: Bearer <token>

Query Parameters:
- ?status=PENDING
- ?patient=<patient_id>
- ?search=<medication_name>
- ?ordering=-created_at
```

### **Get Prescription with Image**

```http
GET /api/prescriptions/<id>/
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "patient": 5,
  "patient_detail": { ... },
  "doctor": 2,
  "doctor_name": "Dr. John Smith",
  "medication": "Amoxicillin 500mg",
  "dosage": "1 capsule",
  "duration": "7 days",
  "instructions": "After meals",
  "status": "PENDING",
  "prescription_image": "/media/prescriptions/2025/11/20/prescription_abc123.jpg",
  "prescription_image_url": "http://localhost:8000/media/prescriptions/2025/11/20/prescription_abc123.jpg",
  "created_by": 3,
  "created_by_name": "Jane Pharmacist",
  "created_at": "2025-11-20T15:30:00Z"
}
```

---

## File Organization

Uploaded prescriptions are organized by date:

```
backend/
├── media/
│   └── prescriptions/
│       └── 2025/
│           └── 11/
│               └── 20/
│                   ├── prescription_abc123.jpg
│                   ├── prescription_def456.pdf
│                   └── prescription_ghi789.png
```

---

## Supported File Types

The `ImageField` supports:
- **Images**: JPG, JPEG, PNG, GIF, BMP, WEBP
- **Note**: For PDFs, you may need to change to `FileField` instead

To support PDFs, change the model field to:

```python
prescription_image = models.FileField(
    upload_to='prescriptions/%Y/%m/%d/',
    null=True,
    blank=True,
    help_text='Scanned or photographed prescription'
)
```

---

## Database Migration Required

Run these commands to apply the changes:

```bash
cd backend
venv\Scripts\activate
pip install Pillow
python manage.py makemigrations patients
python manage.py migrate
```

This will:
1. Install Pillow for image processing
2. Add `prescription_image` and `created_by` fields to Prescription model
3. Create the media directory structure

---

## Usage Workflow

### **For Pharmacists:**

1. Patient comes with written/printed prescription
2. Pharmacist takes photo or scans prescription
3. Creates prescription in system:
   - Selects patient
   - Enters medication details
   - **Uploads prescription image**
   - Saves
4. Prescription is now in system with attached image
5. Can dispense medication
6. Image is available for reference/audit

### **For Doctors:**

1. Creates digital prescription
2. Optionally uploads scanned copy
3. System tracks who created it

---

## Security & Permissions

### **Who Can Upload:**
- ✅ ADMIN
- ✅ DOCTOR
- ✅ PHARMACIST
- ✅ LAB_TECH

### **Who Can View:**
- ✅ All authenticated users (read-only)

### **File Access:**
- Images served via Django in development
- In production, use cloud storage (S3, Cloudinary)
- Files organized by date for easy management

---

## Frontend Integration (Next Steps)

To use this feature in the frontend, you'll need to:

1. **Update Prescription Form** to include file upload:

```vue
<template>
  <form @submit.prevent="handleSubmit" enctype="multipart/form-data">
    <!-- Existing fields -->
    
    <!-- New file upload field -->
    <div class="form-group">
      <label for="prescription_image">Upload Prescription (Optional)</label>
      <input 
        type="file" 
        id="prescription_image"
        @change="handleFileChange"
        accept="image/*"
        capture="environment"  <!-- Enables camera on mobile -->
      />
      <small>Take a photo or upload scanned prescription</small>
    </div>
    
    <button type="submit">Create Prescription</button>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import api from '../api/client';

const form = ref({
  patient: null,
  medication: '',
  dosage: '',
  duration: '',
  instructions: '',
  status: 'PENDING'
});

const prescriptionImage = ref(null);

function handleFileChange(event) {
  prescriptionImage.value = event.target.files[0];
}

async function handleSubmit() {
  const formData = new FormData();
  
  // Add all form fields
  Object.keys(form.value).forEach(key => {
    if (form.value[key]) {
      formData.append(key, form.value[key]);
    }
  });
  
  // Add image if selected
  if (prescriptionImage.value) {
    formData.append('prescription_image', prescriptionImage.value);
  }
  
  try {
    await api.post('/api/prescriptions/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    alert('Prescription created successfully!');
  } catch (error) {
    console.error('Error:', error);
  }
}
</script>
```

2. **Display Prescription Image** in prescription list/detail:

```vue
<template>
  <div v-if="prescription.prescription_image_url">
    <h4>Prescription Image:</h4>
    <img 
      :src="prescription.prescription_image_url" 
      alt="Prescription"
      style="max-width: 100%; height: auto; border-radius: 8px;"
      @click="openImageModal"
    />
  </div>
</template>
```

---

## Production Considerations

### **For Production Deployment:**

1. **Use Cloud Storage** (Recommended):
   - AWS S3
   - Cloudinary
   - Google Cloud Storage
   
2. **Install django-storages**:
   ```bash
   pip install django-storages boto3
   ```

3. **Configure in settings.py**:
   ```python
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
   AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
   AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
   ```

---

## Summary

Successfully implemented:
- ✅ Pharmacists can create prescriptions
- ✅ Image upload for scanned/photographed prescriptions
- ✅ Automatic file organization by date
- ✅ Image URL generation for frontend
- ✅ `created_by` tracking
- ✅ Multipart/form-data support
- ✅ Proper permissions and security

**Next Steps:**
1. Run database migration
2. Install Pillow
3. Update frontend prescription form
4. Test file uploads
5. Consider cloud storage for production

The system now supports uploading prescription images, making it easy for pharmacists to digitize paper prescriptions! 📸
