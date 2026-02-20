from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='doctor_dashboard'),
    path('manage-appointments/', views.manage_appointments, name='manage_appointments'),
    path('update-appointment/<int:appointment_id>/<str:action>/', views.update_appointment_status, name='update_appointment'),
    path('patient-history/<int:patient_id>/', views.patient_history, name='patient_history'),
    path('add-prescription/<int:appointment_id>/', views.add_prescription, name='add_prescription'),
    path('set-availability/', views.set_availability, name='set_availability'),
]