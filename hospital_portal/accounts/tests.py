# accounts/tests.py - Security Testing Suite

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import AuditLog
from django.core import mail

User = get_user_model()

class UserRegistrationTests(TestCase):
    """Test user registration and email verification"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, {
            'email': 'patient@test.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'user_type': 'patient',
            'password1': 'StrongP@ssw0rd123',
            'password2': 'StrongP@ssw0rd123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(email='patient@test.com').exists())
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify Your Email', mail.outbox[0].subject)
    
    def test_duplicate_email_registration(self):
        """Test that duplicate email registration fails"""
        User.objects.create_user(
            email='existing@test.com',
            password='Test123456789',
            first_name='Test',
            last_name='User',
            user_type='patient'
        )
        
        response = self.client.post(self.register_url, {
            'email': 'existing@test.com',
            'first_name': 'Another',
            'last_name': 'User',
            'user_type': 'patient',
            'password1': 'StrongP@ssw0rd123',
            'password2': 'StrongP@ssw0rd123'
        })
        
        self.assertFormError(response, 'form', 'email', 'This email is already registered.')
    
    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected"""
        response = self.client.post(self.register_url, {
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'patient',
            'password1': 'weak',
            'password2': 'weak'
        })
        
        self.assertFormError(response, 'form', 'password2', 
                           'This password is too short. It must contain at least 12 characters.')

class AuthenticationTests(TestCase):
    """Test authentication features"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            email='test@test.com',
            password='StrongP@ssw0rd123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            is_active=True,
            is_verified=True
        )
    
    def test_successful_login(self):
        """Test successful login"""
        response = self.client.post(self.login_url, {
            'email': 'test@test.com',
            'password': 'StrongP@ssw0rd123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Check audit log
        self.assertTrue(AuditLog.objects.filter(
            user=self.user,
            action='login',
            success=True
        ).exists())
    
    def test_failed_login(self):
        """Test failed login attempt"""
        response = self.client.post(self.login_url, {
            'email': 'test@test.com',
            'password': 'WrongPassword'
        })
        
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Check audit log for failed attempt
        self.assertTrue(AuditLog.objects.filter(
            action='failed_login',
            success=False
        ).exists())
    
    def test_inactive_user_cannot_login(self):
        """Test that inactive users cannot login"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.login_url, {
            'email': 'test@test.com',
            'password': 'StrongP@ssw0rd123'
        })
        
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class RateLimitingTests(TestCase):
    """Test rate limiting on login"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            email='test@test.com',
            password='StrongP@ssw0rd123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            is_active=True
        )
    
    def test_rate_limiting_after_failed_attempts(self):
        """Test that rate limiting kicks in after multiple failed attempts"""
        # Make 5 failed login attempts
        for _ in range(5):
            self.client.post(self.login_url, {
                'email': 'test@test.com',
                'password': 'WrongPassword'
            })
        
        # 6th attempt should be rate limited
        response = self.client.post(self.login_url, {
            'email': 'test@test.com',
            'password': 'WrongPassword'
        })
        
        self.assertEqual(response.status_code, 429)  # Too Many Requests

class RoleBasedAccessTests(TestCase):
    """Test role-based access control"""
    
    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            email='patient@test.com',
            password='StrongP@ssw0rd123',
            first_name='Patient',
            last_name='User',
            user_type='patient',
            is_active=True,
            is_verified=True
        )
        
        self.doctor = User.objects.create_user(
            email='doctor@test.com',
            password='StrongP@ssw0rd123',
            first_name='Doctor',
            last_name='User',
            user_type='doctor',
            is_active=True,
            is_verified=True
        )
    
    def test_patient_cannot_access_staff_views(self):
        """Test that patients cannot access staff-only views"""
        self.client.login(email='patient@test.com', password='StrongP@ssw0rd123')
        
        # Try to access a staff-only view (implement this view first)
        # response = self.client.get(reverse('staff_dashboard'))
        # self.assertEqual(response.status_code, 302)  # Redirected
    
    def test_doctor_can_access_staff_views(self):
        """Test that doctors can access staff views"""
        self.client.login(email='doctor@test.com', password='StrongP@ssw0rd123')
        
        # Try to access a staff-only view
        # response = self.client.get(reverse('staff_dashboard'))
        # self.assertEqual(response.status_code, 200)  # Success

class AuditLogTests(TestCase):
    """Test audit logging functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='StrongP@ssw0rd123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            is_active=True
        )
    
    def test_audit_log_creation(self):
        """Test that audit logs are created"""
        initial_count = AuditLog.objects.count()
        
        AuditLog.objects.create(
            user=self.user,
            action='login',
            ip_address='127.0.0.1',
            success=True
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
    
    def test_audit_log_captures_failed_login(self):
        """Test that failed logins are logged"""
        self.client.post(reverse('login'), {
            'email': 'test@test.com',
            'password': 'WrongPassword'
        })
        
        self.assertTrue(AuditLog.objects.filter(
            action='failed_login',
            success=False
        ).exists())

class SessionSecurityTests(TestCase):
    """Test session security features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            password='StrongP@ssw0rd123',
            first_name='Test',
            last_name='User',
            user_type='patient',
            is_active=True,
            is_verified=True
        )
    
    def test_session_expires_after_timeout(self):
        """Test that session expires after configured timeout"""
        self.client.login(email='test@test.com', password='StrongP@ssw0rd123')
        
        # Session should be active
        self.assertTrue(self.client.session.session_key is not None)
        
        # In real scenario, wait for SESSION_COOKIE_AGE to pass
        # Then verify session is expired
    
    def test_logout_clears_session(self):
        """Test that logout properly clears session"""
        self.client.login(email='test@test.com', password='StrongP@ssw0rd123')
        self.assertTrue(self.client.session.session_key is not None)
        
        self.client.get(reverse('logout'))
        
        # Try to access protected page
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected to login

# Run tests with:
# python manage.py test accounts.tests