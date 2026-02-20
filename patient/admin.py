from django.contrib import admin
from .models import PatientProfile, Doctor, Availability, Appointment, MedicalRecord


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_username', 'age', 'gender', 'blood_group']
    list_filter = ['gender', 'blood_group']
    search_fields = ['user__username', 'user__email']

    def get_username(self, obj):
        return obj.user.username

    get_username.short_description = 'Username'


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_full_name', 'specialty', 'hospital', 'is_verified']
    list_filter = ['specialty', 'is_verified', 'hospital']
    search_fields = ['user__first_name', 'user__last_name', 'specialty']
    list_editable = ['is_verified']

    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"

    get_full_name.short_description = 'Doctor Name'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'get_day_display', 'start_time', 'end_time']
    list_filter = ['day', 'doctor']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient_name', 'doctor_name', 'appointment_date', 'status']
    list_filter = ['status', 'appointment_date']
    search_fields = ['patient__username', 'doctor__user__first_name']

    def patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username

    patient_name.short_description = 'Patient'

    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"

    doctor_name.short_description = 'Doctor'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'doctor_name', 'created_at']
    list_filter = ['created_at']

    def patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username

    patient_name.short_description = 'Patient'

    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"

    doctor_name.short_description = 'Doctor'