from django.conf import settings
from django.http import HttpResponsePermanentRedirect

class SSLRedirectExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "SECURE_SSL_REDIRECT", False):
            if not request.path.startswith("/health"):
                if not request.is_secure():
                    return HttpResponsePermanentRedirect("https://" + request.get_host() + request.get_full_path())
        return self.get_response(request)