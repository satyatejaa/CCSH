from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                return redirect('dashboard')
            return redirect('login')
        return wrapper
    return decorator

def patient_required(view_func):
    return role_required(['patient'])(view_func)

def doctor_required(view_func):
    return role_required(['doctor'])(view_func)

def admin_required(view_func):
    return role_required(['admin'])(view_func)