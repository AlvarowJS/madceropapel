"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from channels.routing import URLRouter
from django.urls import path

# from apps.sockets.vistas.documentofirmas import DocumentoFirmas
# from apps.sockets.vistas.documentosubido import DocumentoSubido
from apps.sockets.vistas.conexion import MadCeroPapelConexion

websocket_urlpatterns = [
    path("ws", MadCeroPapelConexion.as_asgi(), name="madceropapel_conexion"),
    # path("ws/documento/cargado/<int:codigo>", DocumentoSubido, name="documento_subido"),
    # path("ws/documento/firmas/<int:pk>/<str:clave>", DocumentoFirmas, name="documento_firmas"),
]
