"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

"""
ASGI config for madceropapel project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

# import os
import django
#
# from channels.routing import get_default_application
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'madceropapel.settings')
# django.setup()
# application = get_default_application()

from .wsgi import *
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import apps.sockets.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'madceropapel.settings')
django.setup()

application = ProtocolTypeRouter({
    # "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(apps.sockets.routing.websocket_urlpatterns)
    ),
    # Just HTTP for now. (We can add other protocols later.)
})
