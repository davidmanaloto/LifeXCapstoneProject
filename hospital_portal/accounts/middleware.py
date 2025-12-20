from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time

class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent brute force attacks
    Limits login attempts per IP address
    """
    
    def process_request(self, request):
        if request.path == '/accounts/login/' and request.method == 'POST':
            ip_address = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip_address}'
            
            # Get current attempts
            attempts = cache.get(cache_key, {'count': 0, 'first_attempt': time.time()})
            
            # Reset if more than 15 minutes have passed
            if time.time() - attempts['first_attempt'] > 900:  # 15 minutes
                attempts = {'count': 0, 'first_attempt': time.time()}
            
            # Check if rate limit exceeded
            if attempts['count'] >= 5:
                time_left = 900 - (time.time() - attempts['first_attempt'])
                minutes_left = int(time_left / 60)
                return HttpResponse(
                    f'Too many login attempts. Please try again in {minutes_left} minutes.',
                    status=429
                )
            
            # Increment attempts
            attempts['count'] += 1
            cache.set(cache_key, attempts, 900)  # 15 minutes expiry
        
        return None
    
    def get_client_ip(self, request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip