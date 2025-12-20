from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from .models import User
from .forms import UserRegistrationForm, UserLoginForm
from .utils import log_audit_event

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Will be activated after email verification
            user.save()
            
            # Send verification email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_link = request.build_absolute_uri(
                reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send email
            try:
                send_mail(
                    'Verify Your Email - Hospital Portal',
                    f'Click the link to verify your email: {verification_link}',
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@hospital.com',
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email sending failed: {e}")
            
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def verify_email(request, uidb64, token):
    """Email verification view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.is_verified = True
        user.save()
        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid verification link.')
        return redirect('register')

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    log_audit_event(user, 'login', request, success=True)
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    return redirect('dashboard')
                else:
                    log_audit_event(user, 'failed_login', request, success=False, 
                                  details={'reason': 'Account not verified'})
                    messages.error(request, 'Your account is not verified. Please check your email.')
            else:
                log_audit_event(None, 'failed_login', request, success=False,
                              details={'email': email, 'reason': 'Invalid credentials'})
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    """User logout view"""
    log_audit_event(request.user, 'logout', request, success=True)
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    """User dashboard view"""
    return render(request, 'dashboard.html', {'user': request.user})

# Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with email verification"""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        # Check if email exists
        email = form.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            messages.error(self.request, 'No account found with this email address.')
            return redirect('password_reset')
        return super().form_valid(form)

def password_reset_done(request):
    """Password reset email sent confirmation"""
    return render(request, 'accounts/password_reset_done.html')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirmation view"""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

def password_reset_complete(request):
    """Password reset complete"""
    return render(request, 'accounts/password_reset_complete.html')