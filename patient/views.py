from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from accounts.decorators import patient_required
from .models import PatientProfile, Doctor, Appointment, MedicalRecord, Availability, Payment
from accounts.models import Hospital
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
@patient_required
def dashboard(request):
    """Patient dashboard showing upcoming and past appointments"""
    today = date.today()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        patient=request.user,
        appointment_date__gte=today,
        status__in=['pending', 'approved']
    ).order_by('appointment_date', 'appointment_time')[:5]

    # Get past appointments
    past_appointments = Appointment.objects.filter(
        patient=request.user,
        status='completed'
    ).order_by('-appointment_date')[:5]

    # Get statistics
    total_appointments = Appointment.objects.filter(patient=request.user).count()
    completed_count = Appointment.objects.filter(
        patient=request.user, 
        status='completed'
    ).count()
    pending_count = Appointment.objects.filter(
        patient=request.user, 
        status='pending'
    ).count()
    cancelled_count = Appointment.objects.filter(
        patient=request.user, 
        status='cancelled'
    ).count()

    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'total_appointments': total_appointments,
        'completed_appointments': completed_count,
        'pending_appointments': pending_count,
        'cancelled_appointments': cancelled_count,
    }
    return render(request, 'patient/dashboard.html', context)


@login_required
@patient_required
def search_doctors(request):
    """Search for doctors by specialty, hospital, or name"""
    # Get filter options
    specialties = Doctor.objects.values_list('specialty', flat=True).distinct().order_by('specialty')
    hospitals = Hospital.objects.filter(is_active=True).order_by('name')

    # Base queryset
    doctors = Doctor.objects.filter(is_verified=True, is_available=True).select_related('user', 'hospital')

    # Apply filters
    specialty = request.GET.get('specialty')
    hospital = request.GET.get('hospital')
    search = request.GET.get('search')

    if specialty:
        doctors = doctors.filter(specialty=specialty)
    if hospital:
        doctors = doctors.filter(hospital_id=hospital)
    if search:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(specialty__icontains=search)
        )

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'hospitals': hospitals,
        'selected_specialty': specialty,
        'selected_hospital': hospital,
        'search_query': search,
    }
    return render(request, 'patient/search_doctors.html', context)


@login_required
@patient_required
def book_appointment(request, doctor_id):
    """Book an appointment with a specific doctor using datetime-local picker"""
    doctor = get_object_or_404(Doctor, id=doctor_id, is_verified=True)

    if request.method == 'POST':
        # Get the datetime from the form
        appointment_datetime = request.POST.get('appointment_datetime')
        symptoms = request.POST.get('symptoms')
        
        # Validate inputs
        if not appointment_datetime:
            messages.error(request, 'Please select date and time.')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        if not symptoms:
            messages.error(request, 'Please describe your symptoms.')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # Split datetime into date and time
        # Format from datetime-local: "YYYY-MM-DDTHH:MM"
        datetime_parts = appointment_datetime.split('T')
        if len(datetime_parts) != 2:
            messages.error(request, 'Invalid date/time format.')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        appointment_date = datetime_parts[0]
        appointment_time = datetime_parts[1] + ':00'  # Add seconds
        
        # Parse the selected datetime
        try:
            selected_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, 'Invalid date/time value.')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # Get current time
        now = datetime.now()
        
        # Check if the selected time is in the future (allow same day with future time)
        if selected_datetime <= now:
            # Format the datetime for display
            formatted_selected = selected_datetime.strftime("%B %d, %Y at %I:%M %p")
            formatted_now = now.strftime("%B %d, %Y at %I:%M %p")
            messages.error(request, f'Please select a future date and time. Selected: {formatted_selected} is not after current time: {formatted_now}')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # Check if selected date is within next 30 days
        max_allowed_date = now + timedelta(days=30)
        
        if selected_datetime > max_allowed_date:
            messages.error(request, 'Please select a date within the next 30 days.')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # Check if doctor is available on this day of week
        selected_date_obj = selected_datetime.date()
        day_of_week = selected_date_obj.weekday()
        
        # Check if doctor has availability for this day
        has_availability = Availability.objects.filter(
            doctor=doctor,
            day=day_of_week,
            is_available=True
        ).exists()
        
        if not has_availability:
            messages.error(request, 'Doctor is not available on this day.')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # Check if the selected time is within doctor's working hours
        availabilities = Availability.objects.filter(
            doctor=doctor,
            day=day_of_week,
            is_available=True
        )
        
        time_obj = selected_datetime.time()
        is_within_hours = False
        working_hours_info = ""
        
        for avail in availabilities:
            start_str = avail.start_time.strftime("%I:%M %p")
            end_str = avail.end_time.strftime("%I:%M %p")
            working_hours_info += f"{start_str} to {end_str}, "
            if avail.start_time <= time_obj <= avail.end_time:
                is_within_hours = True
                break
        
        if not is_within_hours:
            messages.error(request, f'Selected time is outside doctor\'s working hours. Working hours: {working_hours_info}')
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # Check if slot is already booked
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['pending', 'approved']
        ).exists()

        if existing_appointment:
            messages.error(request, 'This time slot is already booked. Please choose another time.')
            return redirect('book_appointment', doctor_id=doctor_id)

        # Create appointment
        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            symptoms=symptoms,
            status='pending'
        )

        messages.success(request, f'Appointment booked successfully! Your appointment ID is {appointment.id}')
        return redirect('my_appointments')

    # For GET request, prepare available dates for reference
    # Get next 30 days for min attribute
    today = date.today()
    max_date = today + timedelta(days=30)
    
    # Calculate min datetime (current date/time)
    now = datetime.now()
    min_datetime = now.strftime('%Y-%m-%dT%H:%M')
    
    # Get doctor's availability summary for next 7 days
    availability_days = []
    for i in range(7):
        check_date = today + timedelta(days=i)
        has_avail = Availability.objects.filter(
            doctor=doctor,
            day=check_date.weekday(),
            is_available=True
        ).exists()
        
        if has_avail:
            # Check if there are any unbooked slots on this day
            availabilities = Availability.objects.filter(
                doctor=doctor,
                day=check_date.weekday(),
                is_available=True
            )
            
            has_free_slots = False
            slot_times = []
            
            for avail in availabilities:
                # Check if any time slot is free
                start = datetime.combine(check_date, avail.start_time)
                end = datetime.combine(check_date, avail.end_time)
                
                while start < end:
                    is_booked = Appointment.objects.filter(
                        doctor=doctor,
                        appointment_date=check_date,
                        appointment_time=start.time(),
                        status__in=['pending', 'approved']
                    ).exists()
                    
                    if not is_booked:
                        has_free_slots = True
                        slot_times.append(start.strftime("%I:%M %p"))
                    start += timedelta(minutes=30)
                
                if has_free_slots:
                    break
            
            if has_free_slots:
                # Get unique times
                slot_times = list(set(slot_times))[:3]  # Show first 3 unique times
                time_display = ", ".join(slot_times)
                
                availability_days.append({
                    'date': check_date,
                    'display': check_date.strftime('%A, %B %d, %Y'),
                    'times': time_display
                })

    context = {
        'doctor': doctor,
        'today': today,
        'max_date': max_date,
        'min_datetime': min_datetime,
        'availability_days': availability_days[:5],  # Show next 5 available days
    }
    return render(request, 'patient/book_appointment.html', context)


@login_required
@patient_required
def my_appointments(request):
    """View all appointments for the logged-in patient"""
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('doctor', 'doctor__user', 'doctor__hospital').order_by('-appointment_date', '-appointment_time')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Get counts for each status
    status_counts = {
        'pending': Appointment.objects.filter(patient=request.user, status='pending').count(),
        'approved': Appointment.objects.filter(patient=request.user, status='approved').count(),
        'completed': Appointment.objects.filter(patient=request.user, status='completed').count(),
        'cancelled': Appointment.objects.filter(patient=request.user, status='cancelled').count(),
    }

    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_counts': status_counts,
    }
    return render(request, 'patient/my_appointments.html', context)


@login_required
@patient_required
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if request.method == 'POST':
        if appointment.status in ['pending', 'approved']:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Appointment cancelled successfully.')
        else:
            messages.error(request, 'This appointment cannot be cancelled.')
        
        return redirect('my_appointments')

    context = {
        'appointment': appointment
    }
    return render(request, 'patient/cancel_appointment.html', context)


@login_required
@patient_required
def medical_history(request):
    """View medical history/records"""
    records = MedicalRecord.objects.filter(
        patient=request.user
    ).select_related('doctor', 'doctor__user', 'appointment').order_by('-created_at')
    
    context = {
        'records': records,
        'total_records': records.count(),
    }
    return render(request, 'patient/medical_history.html', context)


@login_required
@patient_required
def get_available_times(request):
    """AJAX endpoint to get available time slots for a specific date"""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    if not doctor_id or not date_str:
        return JsonResponse({'times': [], 'error': 'Missing parameters'})
    
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Don't allow past dates
        if selected_date < date.today():
            return JsonResponse({'times': [], 'error': 'Cannot select past dates'})
        
        # Get availability for this day
        availabilities = Availability.objects.filter(
            doctor=doctor,
            day=selected_date.weekday(),
            is_available=True
        )
        
        if not availabilities.exists():
            return JsonResponse({'times': [], 'message': 'Doctor not available on this day'})
        
        # Get booked appointments
        booked_times = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=selected_date,
            status__in=['pending', 'approved']
        ).values_list('appointment_time', flat=True)
        
        times = []
        now = datetime.now()
        
        for avail in availabilities:
            start = datetime.combine(selected_date, avail.start_time)
            end = datetime.combine(selected_date, avail.end_time)
            
            # If selected date is today, don't show past times
            if selected_date == date.today():
                if start < now:
                    # Round to next 30 min slot
                    minutes = (now.minute // 30 + 1) * 30
                    if minutes == 60:
                        start = datetime.combine(selected_date, now.time().replace(hour=now.hour+1, minute=0, second=0))
                    else:
                        start = datetime.combine(selected_date, now.time().replace(minute=minutes, second=0))
            
            while start < end:
                time_str = start.strftime('%H:%M')
                display_time = start.strftime('%I:%M %p')
                
                # Don't show past times for today
                if selected_date == date.today() and start < now:
                    start += timedelta(minutes=30)
                    continue
                
                if start.time() not in booked_times:
                    times.append({
                        'value': time_str,
                        'display': display_time
                    })
                start = start + timedelta(minutes=30)
        
        # Sort times
        times.sort(key=lambda x: x['value'])
        
        return JsonResponse({
            'times': times,
            'date': date_str,
            'doctor': doctor_id
        })
        
    except Doctor.DoesNotExist:
        return JsonResponse({'times': [], 'error': 'Doctor not found'})
    except ValueError as e:
        return JsonResponse({'times': [], 'error': 'Invalid date format'})
    except Exception as e:
        print(f"Error in get_available_times: {str(e)}")
        return JsonResponse({'times': [], 'error': str(e)})


@login_required
@patient_required
def reschedule_appointment(request, appointment_id):
    """Reschedule an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    if appointment.status not in ['pending', 'approved']:
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect('my_appointments')
    
    if request.method == 'POST':
        new_datetime = request.POST.get('appointment_datetime')
        
        if not new_datetime:
            messages.error(request, 'Please select new date and time.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        # Split datetime
        datetime_parts = new_datetime.split('T')
        if len(datetime_parts) != 2:
            messages.error(request, 'Invalid date/time format.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        new_date = datetime_parts[0]
        new_time = datetime_parts[1] + ':00'
        
        # Parse the selected datetime
        try:
            selected_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, 'Invalid date/time value.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        # Check if new date is in future
        now = datetime.now()
        if selected_datetime <= now:
            messages.error(request, 'Please select a future date and time.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        # Check if slot is available
        existing = Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=new_date,
            appointment_time=new_time,
            status__in=['pending', 'approved']
        ).exclude(id=appointment_id).exists()
        
        if existing:
            messages.error(request, 'This time slot is already booked.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        # Update appointment
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.status = 'pending'  # Reset to pending for doctor approval
        appointment.save()
        
        messages.success(request, 'Appointment rescheduled successfully!')
        return redirect('my_appointments')
    
    # For GET request
    now = datetime.now()
    min_datetime = now.strftime('%Y-%m-%dT%H:%M')
    
    context = {
        'appointment': appointment,
        'doctor': appointment.doctor,
        'min_datetime': min_datetime,
    }
    return render(request, 'patient/reschedule_appointment.html', context)


# ========== PAYMENT VIEWS ==========
@login_required
@patient_required
def initiate_payment(request, appointment_id):
    """Mock payment for testing (no API keys needed)"""
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Only allow payment for approved appointments
    if appointment.status != 'approved':
        messages.error(request, 'Payment only allowed for approved appointments')
        return redirect('my_appointments')
    
    # Check if payment already exists
    try:
        payment = Payment.objects.get(appointment=appointment)
        if payment.status == 'completed':
            messages.info(request, 'Payment already completed')
            return redirect('payment_success', payment_id=payment.id)
    except Payment.DoesNotExist:
        pass
    
    # Create payment record as completed (for testing)
    payment = Payment.objects.create(
        appointment=appointment,
        patient=request.user,
        doctor=appointment.doctor,
        amount=appointment.doctor.consultation_fee,
        status='completed',
        payment_method='card',
        transaction_id='TEST_' + str(int(datetime.now().timestamp())),
        payment_date=datetime.now(),
        razorpay_payment_id='pay_test_123',
        razorpay_order_id='order_test_123',
        razorpay_signature='test_signature_123'
    )
    
    # Update appointment status
    appointment.status = 'completed'
    appointment.save()
    
    messages.success(request, 'Payment completed successfully! (Test Mode)')
    return redirect('payment_success', payment_id=payment.id)

@csrf_exempt
def payment_callback(request):
    """Handle payment callback from Razorpay"""
    if request.method == 'POST':
        try:
            # Get payment details
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            # Verify signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            # Verify payment signature
            client.utility.verify_payment_signature(params_dict)
            
            # Get payment record
            payment = Payment.objects.get(razorpay_order_id=order_id)
            
            # Update payment status
            payment.status = 'completed'
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.payment_date = datetime.now()
            payment.save()
            
            # Update appointment status
            payment.appointment.status = 'completed'  # Mark as completed after payment
            payment.appointment.save()
            
            messages.success(request, 'Payment completed successfully!')
            return redirect('payment_success', payment_id=payment.id)
            
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found')
        except Exception as e:
            messages.error(request, f'Payment verification failed: {str(e)}')
    
    return redirect('my_appointments')


@login_required
def payment_success(request, payment_id):
    """Show payment success page"""
    payment = get_object_or_404(Payment, id=payment_id, patient=request.user)
    return render(request, 'patient/payment_success.html', {'payment': payment})


@login_required
@patient_required
def payment_history(request):
    """Show patient's payment history"""
    payments = Payment.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'patient/payment_history.html', {'payments': payments})