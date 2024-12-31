"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.tramite.vistas.personal.despacho import PersonalBandejaDespacho, PersonalBandejaDespachoListar, \
    PersonalBandejaDespachoFirmaMasiva, PersonalBandejaDespachoEmisionMasiva, \
    PersonalBandejaDespachoFirmaMasivaEjecutar, PersonalBandejaDespachoFirmaMasivaBajar, \
    PersonalBandejaDespachoFirmaMasivaSubir, PersonalBandejaDespachoFirmaMasivaError
from apps.tramite.vistas.personal.emitido import PersonalBandejaEmitido, PersonalBandejaEmitidosListar
from apps.tramite.vistas.personal.enproyecto import PersonalBandejaEnProyecto, PersonalBandejaEnProyectoListar
from apps.tramite.vistas.personal.entrada import PersonalBandejaEntrada, PersonalBandejaEntradaListar, \
    PersonalBandejaEntradaRecepcionMasiva
from apps.tramite.vistas.personal.firma import PersonalBandejaFirma, PersonalBandejaFirmaVBListar
from apps.tramite.vistas.personal.firmaanexo import PersonalAnexoFirmaVBListar
from apps.tramite.vistas.personal.recepcionado import PersonalBandejaRecepcionado, PersonalBandejaRecepcionadosListar, \
    PersonalBandejaRecepcionadosAtenderMultiple
from apps.tramite.vistas.personal.rechazado import PersonalBandejaRechazado, PersonalBandejaRechazadoListar, \
    PersonalBandejaRechazadoReenviar, PersonalBandejaRechazadoAnular, PersonalBandejaRechazadoArchivar

urlpatterns = [

    # Personal Bandeja Entrada
    path('entrada', PersonalBandejaEntrada.as_view(), name="personal_bandeja_entrada"),
    path('entrada/listar', PersonalBandejaEntradaListar.as_view(), name="personal_bandeja_entrada_listar"),
    path('entrada/recepcionmasiva/vista', PersonalBandejaEntradaRecepcionMasiva.as_view(),
         name="personal_bandeja_entrada_recepcionmasiva"),

    # Personal Bandeja Recepcionados
    path('recepcionado', PersonalBandejaRecepcionado.as_view(), name="personal_bandeja_recepcionado"),
    path('recepcionado/listar/<str:estados>', PersonalBandejaRecepcionadosListar.as_view(),
         name="personal_bandeja_recepcionado_listar"),
    path('recepcionado/atendermultiple/<str:tipo>', PersonalBandejaRecepcionadosAtenderMultiple.as_view(),
         name="personal_bandeja_recepcionados_atender_multiple"),

    # Personal Bandeja Despacho
    path('despacho', PersonalBandejaDespacho.as_view(), name="personal_bandeja_despacho"),
    path('despacho/listar', PersonalBandejaDespachoListar.as_view(), name="personal_bandeja_despacho_listar"),
    path('despacho/firmamasiva/vista', PersonalBandejaDespachoFirmaMasiva.as_view(),
         name="personal_bandeja_despacho_firmamasiva"),
    path('despacho/emisionmasiva/vista', PersonalBandejaDespachoEmisionMasiva.as_view(),
         name="personal_bandeja_despacho_emisionmasiva"),

    # Firma Masiva de Documento
    path('fm/ejecutar', PersonalBandejaDespachoFirmaMasivaEjecutar.as_view(),
         name="personal_bandeja_despacho_firmamasiva_ejecutar"),
    path('fm/bajar/<str:codigo>', PersonalBandejaDespachoFirmaMasivaBajar.as_view(),
         name="personal_bandeja_despacho_firmamasiva_bajar"),
    path('fm/subir/<str:codigo>/<int:emitir>', PersonalBandejaDespachoFirmaMasivaSubir.as_view(),
         name="personal_bandeja_despacho_firmamasiva_subir"),
    path('fm/error/<str:codigo>', PersonalBandejaDespachoFirmaMasivaError.as_view(),
         name="personal_bandeja_despacho_firmamasiva_error"),

    # Personal Bandeja Emitidos
    path('emitido', PersonalBandejaEmitido.as_view(), name="personal_bandeja_emitido"),
    path('emitido/listar', PersonalBandejaEmitidosListar.as_view(), name="personal_bandeja_emitidos_listar"),

    # Personal Bandeja Firmas
    path('firma', PersonalBandejaFirma.as_view(), name="personal_bandeja_firma"),
    path('firma/<str:modo>/listar', PersonalBandejaFirmaVBListar.as_view(), name="personal_bandeja_firma_vb_listar"),

    # Personal Anexo Firmas
    path('firmaanexo/<str:modo>/listar', PersonalAnexoFirmaVBListar.as_view(), name="personal_anexo_firma_vb_listar"),

    # Personal Bandeja En Proyecto
    path('enproyecto', PersonalBandejaEnProyecto.as_view(), name="personal_bandeja_en_proyecto"),
    path('enproyecto/listar', PersonalBandejaEnProyectoListar.as_view(), name="personal_bandeja_en_proyecto_listar"),

    # Personal Bandeja Rechazados
    path('rechazado', PersonalBandejaRechazado.as_view(), name="personal_bandeja_rechazado"),
    path('rechazado/listar', PersonalBandejaRechazadoListar.as_view(), name="personal_bandeja_rechazado_listar"),
    path('rechazado/reenviar/<int:pk>', PersonalBandejaRechazadoReenviar.as_view(),
         name="personal_bandeja_rechazado_reenviar"),
    path('rechazado/anular/<int:pk>', PersonalBandejaRechazadoAnular.as_view(),
         name="personal_bandeja_rechazado_anular"),
    path('rechazado/archivar/<int:pk>', PersonalBandejaRechazadoArchivar.as_view(),
         name="personal_bandeja_rechazado_archivar"),

]
