from .models import AuditLog

def log_audit_event(user, action, request, success=True, details=None):
    """
    Log an audit event
    
    Args:
        user: User instance or None
        action: Action type from AuditLog.ACTION_CHOICES
        request: HttpRequest object
        success: Whether the action was successful
        details: Additional details as dict
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        AuditLog.objects.create(
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details or {}
        )
    except Exception as e:
        # Fail silently to not break the main flow
        print(f"Failed to log audit event: {e}")

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip