from django.db import models


# Doctor models are defined in patient app
# This file is intentionally left mostly empty as we import from patient
# It exists to make Django recognize this as a valid app

# You can add doctor-specific models here if needed in the future
class DoctorNotification(models.Model):
    """Optional: Add doctor-specific notifications"""
    doctor = models.ForeignKey('patient.Doctor', on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']