"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.tramite.vistas.consulta.dni import ConsultaDniPersonaOrigen, ConsultaDniTramitadorOrigen, \
    ConsultaNoDniPersonaOrigen
from apps.tramite.vistas.consulta.ruc import ConsultaRucOrigen
from apps.tramite.vistas.mensajes.externo import MensajePlantillaDocExt
from apps.tramite.vistas.mesapartes.autocomplete import AutoCompleteRazonSocial, AutoCompleteCargo
from apps.tramite.vistas.mesapartes.mensajeria.tablas import MesaPartesMensajeria, MesaPartesMensajeriaTabla, \
    MesaPartesMensajeriaListar
from apps.tramite.vistas.mesapartes.mensajeria.vistas import MesaPartesMensajeriaRecibir, MesaPartesPlanilladoAgregar, \
    MesaPartesMensajeriaDevolver, MesaPartesMensajeriaFinalizarDirecto, MesaPartesMensajeriaImprimir, \
    MesaPartesPlanilladoEditar, MesaPartesPlanilladoDetalle, MesaPartesPlanilladoEliminar, MesaPartesPlanilladoCerrar, \
    MesaPartesPlanilladoExportar, MesaPartesPlanilladoFinalizar, MesaPartesPlanilladoReAbrir, MesaPartesPlanilladoCargo, \
    MesaPartesPlanilladoCargoBajar, MesaPartesMensajeriaImprimirPdfDirecto, MesaPartesPlanilladoRectificar
from apps.tramite.vistas.mesapartes.mimensajeria.vistas import MesaPartesMiMensajeria, MesaPartesMiMensajeriaListar, \
    MesaPartesMiMensajeriaAcciones, MesaPartesMiMensajeriaAccionesFull
from apps.tramite.vistas.mesapartes.registrados import MesaPartesBandejaRegistrados, MesaPartesBandejaRegistradosListar, \
    MesaPartesBandejaRegistradosEmisionMasiva
from apps.tramite.vistas.documento.registrarmesapartes import MesaPartesRegistrar, MesaPartesRegistrarEditar, \
    MesaPartesRegistrarDestinos, MesaPartesRegistrarArchivos, MesaPartesRegistrarArchivosSubir, MesaPartesVerDocumento, \
    MesaPartesRegistrarBotones, MesaPartesRegistrarEmitir, MesaPartesRegistrarEmitirAnular, MesaPartesRegistrarEliminar, \
    MesaPartesRegistrarAnexos, MesaPartesRegistrarAnexoAgregar, MesaPartesRegistrarAnexoEditar, \
    MesaPartesRegistrarAnexoQuitar

urlpatterns = [
    path('consulta/ruc', ConsultaRucOrigen.as_view(), name="consulta_ruc_origen"),
    path('consulta/dniper', ConsultaDniPersonaOrigen.as_view(), name="consulta_dni_persona_origen"),
    path('consulta/nodniper', ConsultaNoDniPersonaOrigen.as_view(), name="consulta_nodni_persona_origen"),
    path('consulta/dnitra', ConsultaDniTramitadorOrigen.as_view(), name="consulta_dni_tramitador_origen"),

    # Autocompletar
    path('mpautocomplete/razonsocial', AutoCompleteRazonSocial.as_view(), name="mp_autocomplete_razonsocial"),
    path('mpautocomplete/cargo', AutoCompleteCargo.as_view(), name="mp_autocomplete_cargo"),

    # Mesa de Partes Bandeja Registrado
    path('registrados', MesaPartesBandejaRegistrados.as_view(), name="mesapartes_registrado"),
    path('registrados/listar/<str:modo>/<str:users>', MesaPartesBandejaRegistradosListar.as_view(),
         name="mesapartes_bandeja_registrados_listar"),
    path('registrados/emisionmasiva/vista', MesaPartesBandejaRegistradosEmisionMasiva.as_view(),
         name="mesapartes_bandeja_registrados_emisionmasiva"),

    # Emitir Documento de Mesa de Partes
    path('registrar', MesaPartesRegistrar.as_view(), name="mesapartes_registrar"),
    path('registrar/editar/<int:pk>', MesaPartesRegistrarEditar.as_view(), name="mesapartes_registrar_editar"),
    path('documento/botones/<int:pk>', MesaPartesRegistrarBotones.as_view(), name="mesapartes_registrar_botones"),
    path('documento/emitir/<int:pk>', MesaPartesRegistrarEmitir.as_view(), name="mesapartes_registrar_emitir"),
    path('documento/emitiranular/<int:pk>', MesaPartesRegistrarEmitirAnular.as_view(),
         name="mesapartes_registrar_emitir_anular"),
    path('documento/eliminar/<int:pk>', MesaPartesRegistrarEliminar.as_view(), name="mesapartes_registrar_eliminar"),
    path('verdoc/<int:iddest>', MesaPartesVerDocumento.as_view(), name="mesapartes_ver_documento"),

    path('registrar/destinos/<int:pk>', MesaPartesRegistrarDestinos.as_view(), name="mesapartes_registrar_destinos"),
    path('registrar/archivos/<int:pk>', MesaPartesRegistrarArchivos.as_view(), name="mesapartes_registrar_archivos"),
    path('registrar/archivos/cargar/<int:iddoc>', MesaPartesRegistrarArchivosSubir,
         name="mesapartes_registrar_archivos_subir"),
    path('registrar/anexos/<int:pk>', MesaPartesRegistrarAnexos.as_view(), name="mesapartes_registrar_anexos"),
    path('registrar/anexos/<int:pk>/agregar', MesaPartesRegistrarAnexoAgregar.as_view(),
         name="mesapartes_registrar_anexo_agregar"),
    path('registrar/anexos/<int:pk>/editar', MesaPartesRegistrarAnexoEditar.as_view(),
         name="mesapartes_registrar_anexo_editar"),
    path('registrar/anexos/<int:pk>/quitar', MesaPartesRegistrarAnexoQuitar.as_view(),
         name="mesapartes_registrar_anexo_quitar"),

    # Plantillas de Mensajes
    path('plantillas/mensajes/documento/externo/<int:pk>', MensajePlantillaDocExt.as_view(),
         name="plantillas_mensajes_docext"),

    # Mensajería
    path('mensajeria', MesaPartesMensajeria.as_view(), name="mesapartes_mensajeria"),
    path('mensajeria/tabla/<str:id>', MesaPartesMensajeriaTabla.as_view(), name="mesapartes_mensajeria_tabla"),
    path('mensajeria/listar/<str:id>/<str:ambito>/<int:padre>', MesaPartesMensajeriaListar.as_view(),
         name="mesapartes_mensajeria_listar"),
    path('mensajeria/recibir/<str:ids>', MesaPartesMensajeriaRecibir.as_view(), name="mesapartes_mensajeria_recibir"),
    path('mensajeria/planillado/agregar/<str:modo>/<str:tipo>/<str:ids>', MesaPartesPlanilladoAgregar.as_view(),
         name="mesapartes_planillado_agregar"),
    path('mensajeria/planillado/editar/<int:pk>', MesaPartesPlanilladoEditar.as_view(),
         name="mesapartes_planillado_editar"),
    path('mensajeria/planillado/eliminar/<int:pk>', MesaPartesPlanilladoEliminar.as_view(),
         name="mesapartes_planillado_eliminar"),
    path('mensajeria/rectificar/<int:pk>', MesaPartesPlanilladoRectificar.as_view(),
         name="mesapartes_planillado_rectificar"),
    path('mensajeria/planillado/cerrar/<int:pk>', MesaPartesPlanilladoCerrar.as_view(),
         name="mesapartes_planillado_cerrar"),
    path('mensajeria/planillado/reabrir/<int:pk>', MesaPartesPlanilladoReAbrir.as_view(),
         name="mesapartes_planillado_reabrir"),
    path('mensajeria/planillado/exportar/<int:pk>', MesaPartesPlanilladoExportar.as_view(),
         name="mesapartes_planillado_exportar"),
    path('mensajeria/planillado/finalizar/<int:pk>', MesaPartesPlanilladoFinalizar.as_view(),
         name="mesapartes_planillado_finalizar"),
    path('mensajeria/planillado/cargo/<int:pk>', MesaPartesPlanilladoCargo.as_view(),
         name="mesapartes_planillado_cargo"),
    path('mensajeria/planillado/cargobajar/<int:pk>', MesaPartesPlanilladoCargoBajar.as_view(),
         name="mesapartes_planillado_cargobajar"),
    path('mensajeria/planillado/detalle/<int:pk>', MesaPartesPlanilladoDetalle.as_view(),
         name="mesapartes_planillado_detalle"),
    path('mensajeria/devolver/<str:ids>', MesaPartesMensajeriaDevolver.as_view(),
         name="mesapartes_mensajeria_devolver"),
    path('mensajeria/finalizadodirecto/<int:desid>', MesaPartesMensajeriaFinalizarDirecto.as_view(),
         name="mesapartes_mensajeria_finalizar_directo"),
    path('mensajeria/imprimir/vista/<int:pk>', MesaPartesMensajeriaImprimir.as_view(),
         name="mesapartes_mensajeria_imprimir"),
    path('mensajeria/imprimir/pdfdir/<int:pk>', MesaPartesMensajeriaImprimirPdfDirecto.as_view(),
         name="mesapartes_mensajeria_imprimir_directo"),

    # Mi Mensajería
    path('mimensajeria', MesaPartesMiMensajeria.as_view(), name="mesapartes_mimensajeria"),
    path('mimensajeria/listar', MesaPartesMiMensajeriaListar.as_view(), name="mesapartes_mimensajeria_listar"),
    path('mimensajeria/acciones/<int:pk>', MesaPartesMiMensajeriaAcciones.as_view(),
         name="mesapartes_mimensajeria_acciones"),
    path('mimensajeria/accionesfull', MesaPartesMiMensajeriaAccionesFull.as_view(),
         name="mesapartes_mimensajeria_accionesfull"),
]
