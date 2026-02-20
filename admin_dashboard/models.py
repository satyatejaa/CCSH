from django.db import models


# This app reuses models from accounts and patient
# No separate models needed, but file must exist for Django

class AdminLog(models.Model):
    """Optional: Track admin actions"""
    ACTION_TYPES = (
        ('verify', 'Verified Doctor'),
        ('hospital', 'Modified Hospital'),
        ('user', 'Modified User'),
    )

    admin = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']