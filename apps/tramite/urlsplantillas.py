"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.tramite.vistas.persona.vista import PersonaVista, PersonaPDFVista
from apps.tramite.vistas.plantillas.comision import ComisionAutorizacionVista
from apps.tramite.vistas.plantillas.destinos import DocumentoDescargarDestVista
from apps.tramite.vistas.plantillas.encargatura import EncargaturaAutorizacionVista, EncargaturaAnulacionVista
from apps.tramite.vistas.plantillas.hojaenvio import HojaEnvioVista
from apps.tramite.vistas.plantillas.proveido import ProveidoVista
from apps.tramite.vistas.plantillas.recepcionfisica import DocumentoRecibirFisicoVista

urlpatterns = [

    # Personal Bandeja Entrada
    path('proveido/<int:iddoc>', ProveidoVista.as_view(), name="plla_proveido_vista"),
    path('hojaenvio/<int:iddoc>', HojaEnvioVista.as_view(), name="plla_hojaenvio_vista"),

    path('encargatura/<int:pk>', EncargaturaAutorizacionVista.as_view(), name="plla_encargatura_vista"),
    path('encargatura/anulacion/<int:pk>', EncargaturaAnulacionVista.as_view(),
         name="plla_encargatura_anulacion_vista"),
    path('comision/<int:pk>', ComisionAutorizacionVista.as_view(), name="plla_comision_vista"),

    path('recepcionfisica/<int:pk>', DocumentoRecibirFisicoVista.as_view(), name="plla_recfis_vista"),

    path('documento/<int:pk>/destinos', DocumentoDescargarDestVista.as_view(), name="plla_docdest_vista"),

    path('persona', PersonaVista.as_view(), name="persona_vista"),
    path('persona/pdf', PersonaPDFVista.as_view(), name="persona_pdf_vista"),
]
