from django.contrib import admin
# Doctor models are in patient app
# This file can be empty or contain doctor-specific admin configurations

# If you want to add doctor-specific admin views:
from patient.models import Doctor, Availability, Appointment

class DoctorInline(admin.StackedInline):
    model = Doctor
    can_delete = False

# You can customize doctor admin here if needed