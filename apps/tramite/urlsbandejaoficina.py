"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.tramite.vistas.oficina.despacho import OficinaBandejaDespacho, OficinaBandejaDespachoListar, \
    OficinaBandejaDespachoFirmaMasiva, OficinaBandejaDespachoFirmaMasivaEjecutar, \
    OficinaBandejaDespachoFirmaMasivaBajar, OficinaBandejaDespachoFirmaMasivaSubir, \
    OficinaBandejaDespachoFirmaMasivaError, OficinaBandejaDespachoEmisionMasiva
from apps.tramite.vistas.oficina.emitido import OficinaBandejaEmitido, OficinaBandejaEmitidosListar
from apps.tramite.vistas.oficina.enproyecto import OficinaBandejaEnProyecto, OficinaBandejaEnProyectoListar
from apps.tramite.vistas.oficina.entrada import OficinaBandejaEntrada, OficinaBandejaEntradaListar, \
    OficinaBandejaEntradaRecepcionMasiva
from apps.tramite.vistas.oficina.firma import OficinaBandejaFirma, OficinaBandejaFirmaVBListar
from apps.tramite.vistas.oficina.firmaanexo import OficinaAnexoFirmaVBListar
from apps.tramite.vistas.oficina.recepcionado import OficinaBandejaRecepcionado, OficinaBandejaRecepcionadosListar, \
    OficinaBandejaRecepcionadosAtender, OficinaBandejaRecepcionadosAtenderMultiple
from apps.tramite.vistas.oficina.rechazado import OficinaBandejaRechazado, OficinaBandejaRechazadoListar, \
    OficinaBandejaRechazadoReenviar, OficinaBandejaRechazadoAnular, OficinaBandejaRechazadoArchivar

urlpatterns = [
    # Oficina Bandeja Entrada
    path('entrada', OficinaBandejaEntrada.as_view(), name="oficina_bandeja_entrada"),
    path('entrada/listar', OficinaBandejaEntradaListar.as_view(), name="oficina_bandeja_entrada_listar"),
    path('entrada/recepcionmasiva/vista', OficinaBandejaEntradaRecepcionMasiva.as_view(),
         name="oficina_bandeja_entrada_recepcionmasiva"),

    # Oficina Bandeja Recepcionados
    path('recepcionado', OficinaBandejaRecepcionado.as_view(), name="oficina_bandeja_recepcionado"),
    path('recepcionado/listar/<str:estados>', OficinaBandejaRecepcionadosListar.as_view(),
         name="oficina_bandeja_recepcionados_listar"),
    path('recepcionado/atender/<int:id>/<str:tipo>', OficinaBandejaRecepcionadosAtender.as_view(),
         name="oficina_bandeja_recepcionados_atender"),
    path('recepcionado/atendermultiple/<str:tipo>/<str:forma>', OficinaBandejaRecepcionadosAtenderMultiple.as_view(),
         name="oficina_bandeja_recepcionados_atender_multiple"),

    # Oficina Bandeja Despacho
    path('despacho', OficinaBandejaDespacho.as_view(), name="oficina_bandeja_despacho"),
    path('despacho/listar', OficinaBandejaDespachoListar.as_view(), name="oficina_bandeja_despacho_listar"),
    path('despacho/firmamasiva/vista', OficinaBandejaDespachoFirmaMasiva.as_view(),
         name="oficina_bandeja_despacho_firmamasiva"),
    path('despacho/emisionmasiva/vista', OficinaBandejaDespachoEmisionMasiva.as_view(),
         name="oficina_bandeja_despacho_emisionmasiva"),

    # Firma Masiva de Documento
    path('fm/ejecutar', OficinaBandejaDespachoFirmaMasivaEjecutar.as_view(),
         name="oficina_bandeja_despacho_firmamasiva_ejecutar"),
    path('fm/bajar/<str:codigo>', OficinaBandejaDespachoFirmaMasivaBajar.as_view(),
         name="oficina_bandeja_despacho_firmamasiva_bajar"),
    path('fm/subir/<str:codigo>/<int:emitir>', OficinaBandejaDespachoFirmaMasivaSubir.as_view(),
         name="oficina_bandeja_despacho_firmamasiva_subir"),
    path('fm/error/<str:codigo>', OficinaBandejaDespachoFirmaMasivaError.as_view(),
         name="oficina_bandeja_despacho_firmamasiva_error"),

    # Oficina Bandeja Emitidos
    path('emitido', OficinaBandejaEmitido.as_view(), name="oficina_bandeja_emitido"),
    path('emitido/listar', OficinaBandejaEmitidosListar.as_view(), name="oficina_bandeja_emitidos_listar"),

    # Oficina Bandeja Firmas
    path('firma', OficinaBandejaFirma.as_view(), name="oficina_bandeja_firma"),
    path('firmavb/<str:modo>/listar', OficinaBandejaFirmaVBListar.as_view(), name="oficina_bandeja_firma_vb_listar"),

    # Oficina Anexo Firmas
    path('firmaanexo/<str:modo>/listar', OficinaAnexoFirmaVBListar.as_view(), name="oficina_anexo_firma_vb_listar"),

    # Oficina Bandeja En Proyecto
    path('enproyecto', OficinaBandejaEnProyecto.as_view(), name="oficina_bandeja_en_proyecto"),
    path('enproyecto/listar', OficinaBandejaEnProyectoListar.as_view(), name="oficina_bandeja_en_proyecto_listar"),

    # Oficina Bandeja Rechazados
    path('rechazado', OficinaBandejaRechazado.as_view(), name="oficina_bandeja_rechazado"),
    path('rechazado/listar', OficinaBandejaRechazadoListar.as_view(), name="oficina_bandeja_rechazado_listar"),
    path('rechazado/reenviar/<int:pk>', OficinaBandejaRechazadoReenviar.as_view(),
         name="oficina_bandeja_rechazado_reenviar"),
    path('rechazado/anular/<int:pk>', OficinaBandejaRechazadoAnular.as_view(),
         name="oficina_bandeja_rechazado_anular"),
    path('rechazado/archivar/<int:pk>', OficinaBandejaRechazadoArchivar.as_view(),
         name="oficina_bandeja_rechazado_archivar"),

]
