from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='patient_dashboard'),
    path('search-doctors/', views.search_doctors, name='search_doctors'),
    path('book-appointment/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('medical-history/', views.medical_history, name='medical_history'),
    path('get-available-times/', views.get_available_times, name='get_available_times'),
    path('reschedule-appointment/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    
    # PAYMENT URLS
    path('payment/<int:appointment_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('payment-success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('payment-history/', views.payment_history, name='payment_history'),
]