from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AgentProfile, OwnerProfile, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'nationality', 'is_email_verified')
    search_fields = ('user__email', 'user__full_name', 'phone_number')
    list_filter = ('is_email_verified', 'nationality')


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'nationality', 'is_email_verified')
    search_fields = ('user__email', 'user__full_name', 'phone_number')
    list_filter = ('is_email_verified', 'nationality')


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('email',)
    ordering = ('-created_at',)
