from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Hospital


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile to display it within User admin
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'phone', 'address')  # Specify fields to show


class CustomUserAdmin(UserAdmin):
    """
    Custom User Admin with profile inline and role display
    """
    inlines = [UserProfileInline]

    # Customize list display
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'is_staff', 'get_role', 'get_phone', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__role']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone']

    def get_role(self, obj):
        """Get user role from profile"""
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return 'No Profile'

    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

    def get_phone(self, obj):
        """Get user phone from profile"""
        try:
            return obj.profile.phone
        except UserProfile.DoesNotExist:
            return 'No Phone'

    get_phone.short_description = 'Phone'
    get_phone.admin_order_field = 'profile__phone'

    # Customize fieldsets for add/change forms
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    """
    Admin configuration for Hospital model
    """
    list_display = ['name', 'city', 'state', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['name', 'city', 'phone', 'email']
    list_editable = ['is_active']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Contact', {
            'fields': ('phone', 'email')
        }),
        ('System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Optional: Add dashboard stats to admin index
admin.site.site_header = 'CareConnect Administration'
admin.site.site_title = 'CareConnect Admin'
admin.site.index_title = 'Healthcare Management System'