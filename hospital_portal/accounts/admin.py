from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, AuditLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ['email', 'get_full_name', 'user_type', 'is_active', 'is_verified', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit Log Admin - Read Only"""
    list_display = ['user_display', 'action', 'ip_address', 'timestamp', 'success_badge']
    list_filter = ['action', 'success', 'timestamp']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['user', 'action', 'ip_address', 'user_agent', 'timestamp', 'details', 'success']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.email} ({obj.user.user_type})"
        return "Anonymous"
    user_display.short_description = 'User'
    
    def success_badge(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    success_badge.short_description = 'Status'