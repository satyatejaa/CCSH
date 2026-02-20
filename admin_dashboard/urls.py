from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('manage-hospitals/', views.manage_hospitals, name='manage_hospitals'),
    path('toggle-hospital/<int:hospital_id>/', views.toggle_hospital_status, name='toggle_hospital'),
    path('verify-doctors/', views.verify_doctors, name='verify_doctors'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('toggle-user/<int:user_id>/', views.toggle_user_status, name='toggle_user'),
    path('analytics/', views.analytics, name='analytics'),
]