from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from datetime import date, datetime, timedelta
from accounts.decorators import doctor_required
from patient.models import Doctor, Appointment, MedicalRecord, Availability
from django.contrib.auth.models import User


@login_required
@doctor_required
def dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    today = date.today()
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status__in=['pending', 'approved']
    ).count()

    total_patients = Appointment.objects.filter(
        doctor=doctor,
        status='completed'
    ).values('patient').distinct().count()

    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).count()

    recent_appointments = Appointment.objects.filter(
        doctor=doctor
    ).order_by('-appointment_date', '-appointment_time')[:10]

    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'total_patients': total_patients,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'doctor/dashboard.html', context)


@login_required
@doctor_required
def manage_appointments(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    status = request.GET.get('status', 'pending')
    date_filter = request.GET.get('date')

    appointments = Appointment.objects.filter(doctor=doctor)

    if status:
        appointments = appointments.filter(status=status)
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    appointments = appointments.order_by('-appointment_date', '-appointment_time')

    context = {
        'appointments': appointments,
        'current_status': status,
    }
    return render(request, 'doctor/manage_appointments.html', context)


@login_required
@doctor_required
def update_appointment_status(request, appointment_id, action):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

    if action == 'approve':
        appointment.status = 'approved'
        messages.success(request, 'Appointment approved successfully.')
    elif action == 'reject':
        appointment.status = 'rejected'
        messages.success(request, 'Appointment rejected.')
    elif action == 'complete':
        appointment.status = 'completed'
        messages.success(request, 'Appointment marked as completed.')

    appointment.save()
    return redirect('manage_appointments')


@login_required
@doctor_required
def patient_history(request, patient_id):
    doctor = get_object_or_404(Doctor, user=request.user)
    patient = get_object_or_404(User, id=patient_id)

    # Check if doctor has treated this patient
    has_treated = Appointment.objects.filter(
        doctor=doctor,
        patient=patient,
        status='completed'
    ).exists()

    if not has_treated:
        messages.error(request, 'You do not have permission to view this patient\'s history.')
        return redirect('doctor_dashboard')

    appointments = Appointment.objects.filter(
        doctor=doctor,
        patient=patient
    ).order_by('-appointment_date')

    medical_records = MedicalRecord.objects.filter(
        patient=patient,
        doctor=doctor
    ).order_by('-created_at')

    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    return render(request, 'doctor/patient_history.html', context)


@login_required
@doctor_required
def add_prescription(request, appointment_id):
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis')
        prescription = request.POST.get('prescription')
        notes = request.POST.get('notes')

        MedicalRecord.objects.create(
            patient=appointment.patient,
            doctor=doctor,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
            appointment=appointment
        )

        appointment.status = 'completed'
        appointment.save()

        messages.success(request, 'Prescription added successfully.')
        return redirect('manage_appointments')

    context = {
        'appointment': appointment,
    }
    return render(request, 'doctor/add_prescription.html', context)


@login_required
@doctor_required
def set_availability(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        # Clear existing availability
        Availability.objects.filter(doctor=doctor).delete()

        days = request.POST.getlist('days[]')
        start_times = request.POST.getlist('start_time[]')
        end_times = request.POST.getlist('end_time[]')

        for i in range(len(days)):
            if days[i] and start_times[i] and end_times[i]:
                Availability.objects.create(
                    doctor=doctor,
                    day=int(days[i]),
                    start_time=start_times[i],
                    end_time=end_times[i]
                )

        messages.success(request, 'Availability updated successfully.')
        return redirect('set_availability')

    availabilities = Availability.objects.filter(doctor=doctor).order_by('day')

    context = {
        'availabilities': availabilities,
        'days_range': range(7),
    }
    return render(request, 'doctor/set_availability.html', context)