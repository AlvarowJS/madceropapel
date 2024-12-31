"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.utils import timezone
from rest_framework.authtoken.models import Token


class RestFrameworkTokenMiddleware(object):

    def __init__(self, next_layer=None):
        self.get_response = next_layer

    def process_request(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, "persona"):
                if hasattr(request.user, "auth_token"):
                    vence = request.user.auth_token.created + timezone.timedelta(hours=12)
                    ahora = timezone.now()
                    if ahora > vence:
                        token = request.user.auth_token
                        token.delete()
                        token.key = token.generate_key()
                        token.save()
        pass

    def process_response(self, request, response):
        return response

    def __call__(self, request):
        response = self.process_request(request)
        if response is None:
            response = self.get_response(request)
        response = self.process_response(request, response)
        return response
