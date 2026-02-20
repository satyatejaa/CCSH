from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from datetime import date, timedelta
from accounts.decorators import admin_required
from accounts.models import User, UserProfile, Hospital
from patient.models import Doctor, PatientProfile, Appointment, MedicalRecord
from django.contrib.auth.models import User


@login_required
@admin_required
def dashboard(request):
    total_users = User.objects.count()
    total_patients = UserProfile.objects.filter(role='patient').count()
    total_doctors = UserProfile.objects.filter(role='doctor').count()
    total_hospitals = Hospital.objects.count()

    today = date.today()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    pending_doctors = Doctor.objects.filter(is_verified=False).count()

    recent_appointments = Appointment.objects.order_by('-created_at')[:10]

    # Get top doctors
    top_doctors = Doctor.objects.annotate(
        appointment_count=Count('doctor_appointments', filter=Q(doctor_appointments__status='completed'))
    ).order_by('-appointment_count')[:5]

    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_hospitals': total_hospitals,
        'today_appointments': today_appointments,
        'pending_doctors': pending_doctors,
        'recent_appointments': recent_appointments,
        'top_doctors': top_doctors,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@admin_required
def manage_hospitals(request):
    hospitals = Hospital.objects.all().order_by('-created_at')

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        Hospital.objects.create(
            name=name,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            phone=phone,
            email=email
        )

        messages.success(request, 'Hospital added successfully.')
        return redirect('manage_hospitals')

    context = {'hospitals': hospitals}
    return render(request, 'admin_dashboard/manage_hospitals.html', context)


@login_required
@admin_required
def toggle_hospital_status(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    hospital.is_active = not hospital.is_active
    hospital.save()
    messages.success(request, f'Hospital status updated.')
    return redirect('manage_hospitals')


@login_required
@admin_required
def verify_doctors(request):
    doctors = Doctor.objects.filter(is_verified=False).select_related('user', 'hospital')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        action = request.POST.get('action')

        doctor = get_object_or_404(Doctor, id=doctor_id)

        if action == 'verify':
            doctor.is_verified = True
            doctor.save()
            messages.success(request, f'Dr. {doctor.user.get_full_name()} has been verified.')
        elif action == 'reject':
            # Optionally delete or mark as rejected
            messages.warning(request, f'Dr. {doctor.user.get_full_name()} has been rejected.')

    context = {'doctors': doctors}
    return render(request, 'admin_dashboard/verify_doctors.html', context)


@login_required
@admin_required
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')

    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(profile__role=role_filter)

    context = {
        'users': users,
        'role_filter': role_filter,
    }
    return render(request, 'admin_dashboard/manage_users.html', context)


@login_required
@admin_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f'User status updated.')
    return redirect('manage_users')


@login_required
@admin_required
def analytics(request):
    # Appointments trend (last 7 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=6)

    appointments_trend = Appointment.objects.filter(
        appointment_date__range=[start_date, end_date]
    ).annotate(
        date=TruncDate('appointment_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Appointment status distribution
    status_distribution = Appointment.objects.values('status').annotate(
        count=Count('id')
    )

    # Top doctors by appointments
    top_doctors = Doctor.objects.annotate(
        appointment_count=Count('doctor_appointments')
    ).order_by('-appointment_count')[:10]

    # Patient demographics
    patient_gender = PatientProfile.objects.values('gender').annotate(
        count=Count('id')
    )

    context = {
        'appointments_trend': appointments_trend,
        'status_distribution': status_distribution,
        'top_doctors': top_doctors,
        'patient_gender': patient_gender,
        'total_appointments': Appointment.objects.count(),
        'completed_appointments': Appointment.objects.filter(status='completed').count(),
        'cancelled_appointments': Appointment.objects.filter(status='cancelled').count(),
    }
    return render(request, 'admin_dashboard/analytics.html', context)