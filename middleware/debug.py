from django.views.debug import technical_500_response
import sys
from django.conf import settings

class UserBasedExceptionMiddleware(object):
    def process_exception(self, request, exception):
        if request.user.is_superuser and request.META.get('REMOTE_ADDR') in getattr(settings, 'INTERNAL_IPS', []):
            return technical_500_response(request, *sys.exc_info())

