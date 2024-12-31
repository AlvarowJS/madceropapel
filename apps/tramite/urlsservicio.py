"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.tramite.vistas.servicio.documento import ServicioDocumentoValida, ServicioSeguimientoExp, \
    ServicioSeguimientoNodo, ServicioSeguimientoInfo
from apps.tramite.vistas.servicio.generatoken import SeguridadAutenticacion
from apps.tramite.vistas.servicio.registro import RegistroAgregar, RegistroUOListar
from apps.tramite.vistas.servicio.usuario import UsuarioToken, UsuarioLogin, UsuarioInfo

urlpatterns = [
    path('token', SeguridadAutenticacion.as_view(), name="token"),

    # Servicio de Seguimiento
    path('documento/<int:anio>/<int:numero>/<str:clave>', ServicioDocumentoValida.as_view(),
         name="servicio_documento_valida"),
    path('seguimiento/root/<int:anio>/<int:numero>/<str:clave>', ServicioSeguimientoExp.as_view(),
         name="servicio_seguimiento_exp"),
    path('seguimiento/nodo/<str:modo>/<int:id>', ServicioSeguimientoNodo.as_view(), name="servicio_seguimiento_nodo"),
    path('seguimiento/info/<str:modo>/<int:id>', ServicioSeguimientoInfo.as_view(), name="servicio_seguimiento_info"),

    # Servicio para agregar documentos de manera externa
    path('usuario/login/<str:username>/<str:password>', UsuarioLogin.as_view(), name="usuario_login"),
    path('usuario/info/<str:dni>', UsuarioInfo.as_view(), name="usuario_info"),
    path('usuario/token/<str:dni>', UsuarioToken.as_view(), name="usuario_token"),
    path('registro/uolistar', RegistroUOListar.as_view(), name="registro_uo_listar"),
    path('registro/agregar', RegistroAgregar.as_view(), name="registro_agregar")

]
