# accounts/urls.py - Complete URL patterns

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    
    # Password Reset
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # Two-Factor Authentication
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    
    # Audit Logs (Admin only)
    path('audit-logs/', views.audit_log_view, name='audit_logs'),
]

# hospital_portal/urls.py - Main URL configuration

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('', account_views.user_login, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)