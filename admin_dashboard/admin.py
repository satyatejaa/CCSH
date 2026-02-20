from django.contrib import admin
from .models import AdminLog


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for tracking admin actions
    """
    list_display = ['admin', 'action_type', 'description_short', 'timestamp']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['admin__username', 'description']
    readonly_fields = ['admin', 'action_type', 'description', 'timestamp']

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description

    description_short.short_description = 'Description'

    def has_add_permission(self, request):
        return False  # Don't allow manual addition

    def has_change_permission(self, request, obj=None):
        return False  # Don't allow changes to logs