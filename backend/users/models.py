from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DOCTOR = "DOCTOR", "Doctor"
        LAB_TECH = "LAB_TECH", "Lab Tech"
        PHARMACIST = "PHARMACIST", "Pharmacist"
        FINANCE = "FINANCE", "Finance"
        PATIENT = "PATIENT", "Patient"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
