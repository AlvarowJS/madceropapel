"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.tramite.vistas.seguimiento.consulta import SeguimientoExp, Seguimiento, SeguimientoNodo, SeguimientoInfo

urlpatterns = [
    path('exp/<str:dep>/<int:anio>/<int:num>', SeguimientoExp.as_view(), name="seguimiento_exp"),
    path('padre/<str:modo>/<int:id>', Seguimiento.as_view(), name="seguimiento"),
    path('nodo/<int:id>', SeguimientoNodo.as_view(), name="seguimiento_nodo"),
    path('info/<str:modo>/<int:id>', SeguimientoInfo.as_view(), name="seguimiento_info"),
]