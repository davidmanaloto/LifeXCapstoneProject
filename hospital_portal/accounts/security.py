# accounts/security.py - SSRF Protection utilities

import ipaddress
import socket
from urllib.parse import urlparse
from django.core.exceptions import ValidationError

def is_safe_url(url):
    """
    Validate URL to prevent SSRF attacks
    Blocks internal IP addresses and localhost
    """
    try:
        parsed = urlparse(url)
        
        # Must have http or https scheme
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Get hostname
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Resolve hostname to IP
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            return False
        
        # Check if IP is private/internal
        ip_obj = ipaddress.ip_address(ip)
        
        # Block private IPs
        if ip_obj.is_private:
            return False
        
        # Block localhost
        if ip_obj.is_loopback:
            return False
        
        # Block link-local addresses
        if ip_obj.is_link_local:
            return False
        
        # Block reserved addresses
        if ip_obj.is_reserved:
            return False
        
        return True
        
    except Exception:
        return False

def validate_external_url(url):
    """
    Validator for URL fields
    Use in forms or model fields
    """
    if not is_safe_url(url):
        raise ValidationError(
            'This URL is not allowed for security reasons. '
            'Internal and private network URLs are blocked.'
        )

# Example usage in views
import requests
from django.http import JsonResponse

def fetch_external_data(request):
    """
    Example: Fetching data from external API
    """
    url = request.GET.get('url')
    
    # SSRF Protection
    if not is_safe_url(url):
        return JsonResponse({
            'error': 'Invalid or unsafe URL'
        }, status=400)
    
    try:
        # Add timeout to prevent hanging
        response = requests.get(url, timeout=5)
        return JsonResponse({
            'data': response.text
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'error': 'Failed to fetch data'
        }, status=500)

# Example: AI Integration with SSRF protection
def call_ai_api(request):
    """
    Example: Calling AI API for medical record generation
    """
    # Whitelist of allowed AI API endpoints
    ALLOWED_AI_ENDPOINTS = [
        'https://api.openai.com',
        'https://api.anthropic.com',
        # Add your AI service here
    ]
    
    api_url = request.POST.get('api_url')
    
    # Validate against whitelist
    parsed = urlparse(api_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    if base_url not in ALLOWED_AI_ENDPOINTS:
        return JsonResponse({
            'error': 'Unauthorized API endpoint'
        }, status=403)
    
    # Additional SSRF check
    if not is_safe_url(api_url):
        return JsonResponse({
            'error': 'Invalid API URL'
        }, status=400)
    
    # Safe to proceed
    # ... make API call ...