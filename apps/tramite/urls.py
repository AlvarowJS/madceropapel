"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path, include

from apps.tramite.vistas.consulta.dni import ConsultaDniTrabajador, ConsultaDniPersona
from apps.tramite.vistas.consulta.expedienteref import ConsultaExpedienteRef
from apps.tramite.vistas.consulta.ruc import ConsultaRucDestino, ConsultaRazonSocial
from apps.tramite.vistas.correlativo.correlativo import CorrelativoVista, CorrelativoListar, CorrelativoCambiar
from apps.tramite.vistas.distribuidor import DistribuidorInicio, DistribuidorListar, DistribuidorAgregar, \
    DistribuidorEditar, DistribuidorConsultaRuc, DistribuidorConsultaDni, DistribuidorEliminar
from apps.tramite.vistas.documento.archivar import DocumentoArchivar, DocumentoDesarchivar
from apps.tramite.vistas.documento.confidencial import DocumentoConfidencialSolicitarPermiso, \
    DocumentoConfidencialAcceder
from apps.tramite.vistas.documento.detalles import DocumentoDestinoVista, DocumentoFirmaVista, DocumentoReferenciaVista, \
    DocumentoAnexoAgregarVista, DocumentoReferenciaPdfVista, DocumentoAnexoDescargarVista, DocumentoAnexoEditarVista, \
    DocumentoAnexoQuitarVista, DocumentoAnexoListarVista, DocumentoAnexoImportarVista, DocumentoDestinoCargosVista
from apps.tramite.vistas.documento.anexo import DocumentoAnexoFirmarVB, DocumentoAnexoFirmarVBBajar, \
    DocumentoAnexoFirmarVBSubir, DocumentoAnexoFirmarVBError, DocumentoDestinoEntFisVista, \
    DocumentoAnexoMasivoAgregarVista, DocumentoAnexoFirmarVBM, DocumentoAnexoFirmarVBMBajar, \
    DocumentoAnexoFirmarVBMSubir, DocumentoAnexoFirmarVBMError, DocumentoAnexoReset
from apps.tramite.vistas.documento.detalleslistas import DocumentoDestinoUOListar, DocumentoDestinoPTListar, \
    DocumentoReferenciaDepListar, DocumentoResponsableListar, DocumentoTipoListar
from apps.tramite.vistas.documento.emitir import DocumentoEmitir, DocumentoEmitirEditar, DocumentoEmitirGenerar, \
    DocumentoEmitirGenerarBajar, DocumentoEmitirGenerarSubir, DocumentoEmitirGenerarError, DocumentoEmitirBotones, \
    DocumentoEmitirDespacho, DocumentoEmitirEnviar, DocumentoEmitirAnular, DocumentoEmitirAnularEmision, \
    DocumentoEmitirObservar, DocumentoEmitirCambiarResponsable
from apps.tramite.vistas.documento.emitirfirmar import DocumentoEmitirFirmar, DocumentoEmitirFirmarBajar, \
    DocumentoEmitirFirmarSubir, DocumentoEmitirFirmarError, DocumentoEmitirFirmarVB, DocumentoEmitirFirmarVBBajar, \
    DocumentoEmitirFirmarVBSubir, DocumentoEmitirFirmarVBError, DocumentoDescargar, DocumentoEmitirFirmarVBObservar, \
    DocumentoAnexos, DocumentoDescargar2, DocumentoDescargarFast, DocumentoDescargarFull, DocumentoDescargarDest, \
    DocumentoReferencias
from apps.tramite.vistas.documento.grupos import DocumentoDestinoGrupo, DocumentoDestinoGrupoListar
from apps.tramite.vistas.documento.rechazar import DocumentoRechazar
from apps.tramite.vistas.documento.recibir import DocumentoRecibir, DocumentoRecibirAnular, DocumentoRecibirFisico, \
    DocumentoRecibirFisicoBajar, DocumentoRecibirFisicoSubir, DocumentoRecibirFisicoError, DocumentoRecibirFisicoQR, \
    DocumentoRecibirFisicoQRSubir, DocumentoRecFisDoc, DocumentoRecibirFisicoMasivoBajar, \
    DocumentoRecibirFisicoMasivoSubir, DocumentoRecibirFisicoMasivoError, DocumentoRecibirFisicoMasivoGenerar
from apps.tramite.vistas.documento.visar import DocumentoVisar
from apps.tramite.vistas.misencargaturas.misencargaturas import MisEncargaturas, MisEncargaturasListar
from apps.tramite.vistas.privado.privado import PrivadoInfo

app_name = "apptra"

urlpatterns = [
    # Consulta RUC con combo
    path('consulta/ruc', ConsultaRucDestino.as_view(), name="consulta_ruc_destino"),
    path('consulta/razonsocial', ConsultaRazonSocial.as_view(), name="consulta_razonsocial"),

    # Consulta DNI con combo
    path('consulta/dniper', ConsultaDniPersona.as_view(), name="consulta_dni_persona"),
    path('consulta/dnitra', ConsultaDniTrabajador.as_view(), name="consulta_dni_trabajador"),

    # Consulta Expediente
    path('consulta/expedienteref', ConsultaExpedienteRef.as_view(), name="consulta_expediente_ref"),

    # Documento Privado
    path('privado/info', PrivadoInfo.as_view(), name="privado_info"),

    # Distribuidores
    path('distribuidor', DistribuidorInicio.as_view(), name="distribuidor_inicio"),
    path('distribuidor/listar', DistribuidorListar.as_view(), name="distribuidor_listar"),
    path('distribuidor/agregar', DistribuidorAgregar.as_view(), name="distribuidor_agregar"),
    path('distribuidor/<int:pk>/editar', DistribuidorEditar.as_view(), name="distribuidor_editar"),
    path('distribuidor/<int:pk>/eliminar', DistribuidorEliminar.as_view(), name="distribuidor_eliminar"),

    path('distribuidor/consulta/ruc', DistribuidorConsultaRuc.as_view(), name="distribuidor_consulta_ruc"),
    path('distribuidor/consulta/dni', DistribuidorConsultaDni.as_view(), name="distribuidor_consulta_dni"),

    # Emitir Documento
    path('documento/descargar/<int:pk>/<int:cod>', DocumentoDescargar.as_view(), name="documento_descargar"),
    path('documento/descargar/<int:pk>', DocumentoDescargar.as_view(), name="documento_descargar"),
    path('documento/descargarfast/<int:pk>', DocumentoDescargarFast.as_view(), name="documento_descargar_fast"),
    path('documento/descargar2/<str:ori>/<int:cod>', DocumentoDescargar2.as_view(), name="documento_descargar_2"),
    path('documento/anexos/<int:pk>', DocumentoAnexos.as_view(), name="documento_anexos"),
    path('documento/referencias/<int:pk>', DocumentoReferencias.as_view(), name="documento_referencias"),
    path('documento/descargarfull/<int:pk>', DocumentoDescargarFull.as_view(), name="documento_descargar_full"),
    path('documento/descargardest/<int:pk>', DocumentoDescargarDest.as_view(), name="documento_descargar_dest"),

    path('documento/confidencial/solicitarpermiso', DocumentoConfidencialSolicitarPermiso.as_view(),
         name="documento_confidencial_solicitarpermiso"),
    path('documento/confidencial/acceder', DocumentoConfidencialAcceder.as_view(),
         name="documento_confidencial_acceder"),

    path('documento/emitir/<str:tipo>', DocumentoEmitir.as_view(), name="documento_emitir"),
    path('documento/editar/<int:pk>/<str:tab>/<int:tabid>', DocumentoEmitirEditar.as_view(),
         name="documento_emitir_editar"),
    path('documento/responsablecambiar/<int:pk>', DocumentoEmitirCambiarResponsable.as_view(),
         name="documento_emitir_cambiar_responsable"),

    path('documento/observar/<int:pk>', DocumentoEmitirObservar.as_view(), name="documento_emitir_observar"),
    path('documento/anular/<int:pk>', DocumentoEmitirAnular.as_view(), name="documento_emitir_anular"),
    path('documento/anularemision/<int:pk>', DocumentoEmitirAnularEmision.as_view(),
         name="documento_emitir_anular_emision"),

    path('documento/emitir/despacho/<int:pk>', DocumentoEmitirDespacho.as_view(), name="documento_emitir_despacho"),
    path('documento/emitir/enviar/<int:pk>', DocumentoEmitirEnviar.as_view(), name="documento_emitir_enviar"),

    path('documento/botones/<int:pk>', DocumentoEmitirBotones.as_view(), name="documento_emitir_botones"),

    path('documento/recibir/<int:pk>', DocumentoRecibir.as_view(), name="documento_recibir"),
    path('documento/recibirfisico/<int:pk>/generar', DocumentoRecibirFisico.as_view(), name="documento_recibirf_g"),
    path('documento/recibirfisico/<int:pk>/qr', DocumentoRecibirFisicoQR.as_view(), name="documento_recibirf_qr"),
    path('documento/recibirfisico/<str:codigo>/qr/subir', DocumentoRecibirFisicoQRSubir.as_view(),
         name="documento_recibirf_qr_subir"),

    path('documento/recibirfisico/<int:pk>/<int:ptid>/bajar', DocumentoRecibirFisicoBajar.as_view(),
         name="documento_recibirf_b"),
    path('documento/recibirfisico/<int:pk>/subir', DocumentoRecibirFisicoSubir.as_view(), name="documento_recibirf_s"),
    path('documento/recibirfisico/<int:pk>/error', DocumentoRecibirFisicoError.as_view(), name="documento_recibirf_e"),
    path('documento/recibirfisicom/<str:codigos>/generar', DocumentoRecibirFisicoMasivoGenerar.as_view(),
         name="documento_recibirfm_g"),
    path('documento/recibirfisicom/<str:codigo>/<int:ptid>/bajar', DocumentoRecibirFisicoMasivoBajar.as_view(),
         name="documento_recibirfm_b"),
    path('documento/recibirfisicom/<str:codigo>/subir', DocumentoRecibirFisicoMasivoSubir.as_view(),
         name="documento_recibirfm_s"),
    path('documento/recibirfisicom/<str:codigo>/error', DocumentoRecibirFisicoMasivoError.as_view(),
         name="documento_recibirfm_e"),
    path('documento/recibiranular/<int:pk>', DocumentoRecibirAnular.as_view(), name="documento_recibir_anular"),

    path('documento/archivar/<int:pk>', DocumentoArchivar.as_view(), name="documento_archivar"),
    path('documento/desarchivar/<int:pk>', DocumentoDesarchivar.as_view(), name="documento_desarchivar"),
    path('documento/rechazar/<int:pk>', DocumentoRechazar.as_view(), name="documento_rechazar"),

    path('documento/generar/<int:pk>', DocumentoEmitirGenerar.as_view(), name="documento_emitir_generar"),
    path('documento/generar/bajar/<str:codigo>', DocumentoEmitirGenerarBajar.as_view(),
         name="documento_emitir_generar_bajar"),
    path('documento/generar/subir/<str:codigo>', DocumentoEmitirGenerarSubir.as_view(),
         name="documento_emitir_generar_subir"),
    path('documento/generar/error/<str:codigo>', DocumentoEmitirGenerarError.as_view(),
         name="documento_emitir_generar_error"),
    # Firmas
    path('documento/firmar/<int:pk>', DocumentoEmitirFirmar.as_view(), name="documento_emitir_firmar"),
    path('documento/firmar/bajar/<str:codigo>', DocumentoEmitirFirmarBajar.as_view(),
         name="documento_emitir_firmar_bajar"),
    path('documento/firmar/subir/<str:codigo>', DocumentoEmitirFirmarSubir.as_view(),
         name="documento_emitir_firmar_subir"),
    path('documento/firmar/error/<str:codigo>', DocumentoEmitirFirmarError.as_view(),
         name="documento_emitir_firmar_error"),

    # Firma Adicional o VB
    path('documento/firmarvb/<int:pk>', DocumentoEmitirFirmarVB.as_view(), name="documento_emitir_firmarvb"),
    path('documento/firmarvb/bajar/<str:codigo>', DocumentoEmitirFirmarVBBajar.as_view(),
         name="documento_emitir_firmarvb_bajar"),
    path('documento/firmarvb/subir/<str:codigo>', DocumentoEmitirFirmarVBSubir.as_view(),
         name="documento_emitir_firmarvb_subir"),
    path('documento/firmarvb/error/<str:codigo>', DocumentoEmitirFirmarVBError.as_view(),
         name="documento_emitir_firmarvb_error"),

    # Firma Adicional o VB
    path('documento/firmarvb/<int:pk>', DocumentoEmitirFirmarVB.as_view(), name="documento_emitir_firmarvb"),
    path('documento/firmarvb/bajar/<str:codigo>', DocumentoEmitirFirmarVBBajar.as_view(),
         name="documento_emitir_firmarvb_bajar"),
    path('documento/firmarvb/subir/<str:codigo>', DocumentoEmitirFirmarVBSubir.as_view(),
         name="documento_emitir_firmarvb_subir"),
    path('documento/firmarvb/error/<str:codigo>', DocumentoEmitirFirmarVBError.as_view(),
         name="documento_emitir_firmarvb_error"),
    path('documento/firmarvb/observar/<int:pk>', DocumentoEmitirFirmarVBObservar.as_view(),
         name="documento_emitir_firmarvb_observar"),

    # Datos Adicionales al Documento
    path('documento/detalle/destino', DocumentoDestinoVista.as_view(), name="documento_destinos"),
    path('documento/detalle/destino/cargos', DocumentoDestinoCargosVista.as_view(), name="documento_destinos_cargos"),
    path('documento/detalle/referencia', DocumentoReferenciaVista.as_view(), name="documento_referencias"),
    path('documento/detalle/referencia/pdf/<str:origen>/<str:nro>/<str:emi>/<int:dest>',
         DocumentoReferenciaPdfVista.as_view(), name="documento_referencia_pdf"),
    path('documento/detalle/referencia/pdf/<str:origen>/<str:nro>/<str:emi>/<int:dest>/<int:down>',
         DocumentoReferenciaPdfVista.as_view(), name="documento_referencia_pdfdown"),
    path('documento/detalle/firma', DocumentoFirmaVista.as_view(), name="documento_firmas"),

    path('documento/detalle/grupo/<str:tipo>', DocumentoDestinoGrupo.as_view(), name="documento_destino_grupo"),
    path('documento/detalle/grupo/<str:tipo>/listar', DocumentoDestinoGrupoListar.as_view(),
         name="documento_destino_grupo_listar"),

    path('documento/detalle/destino/entfis/<int:pk>', DocumentoDestinoEntFisVista.as_view(),
         name="documento_destino_entregafisica"),

    path('documento/detalle/anexo/agregar/<int:pk>', DocumentoAnexoAgregarVista.as_view(),
         name="documento_anexo_agregar"),
    path('documento/detalle/anexo/editar/<int:pk>', DocumentoAnexoEditarVista.as_view(),
         name="documento_anexo_editar"),
    path('documento/detalle/anexo/quitar/<int:pk>', DocumentoAnexoQuitarVista.as_view(),
         name="documento_anexo_quitar"),
    path('documento/detalle/anexo/importar/<int:pk>', DocumentoAnexoImportarVista.as_view(),
         name="documento_anexo_importar"),
    path('documento/detalle/anexo/descargar/<int:pk>', DocumentoAnexoDescargarVista.as_view(),
         name="documento_anexo_descargar"),
    path('documento/detalle/anexo/listar/<int:pk>', DocumentoAnexoListarVista.as_view(),
         name="documento_anexo_listar"),
    path('documento/detalle/anexo/masivo/agregar/<int:pk>', DocumentoAnexoMasivoAgregarVista.as_view(),
         name="documento_anexo_masivo_agregar"),

    # Anexo Firma/VB
    path('documento/detalle/anexo/firmarvb/<int:pk>', DocumentoAnexoFirmarVB.as_view(),
         name="documento_anexo_firmarvb"),
    path('documento/detalle/anexo/firmarvb/bajar/<str:codigo>', DocumentoAnexoFirmarVBBajar.as_view(),
         name="documento_anexo_firmarvb_bajar"),
    path('documento/detalle/anexo/firmarvb/subir/<str:codigo>', DocumentoAnexoFirmarVBSubir.as_view(),
         name="documento_anexo_firmarvb_subir"),
    path('documento/detalle/anexo/firmarvb/error/<str:codigo>', DocumentoAnexoFirmarVBError.as_view(),
         name="documento_anexo_firmarvb_error"),
    path('documento/detalle/anexo/reset/<int:pk>', DocumentoAnexoReset.as_view(),
         name="documento_anexo_reset"),

    # Anexo Firma/VB - Masivo
    path('documento/detalle/anexo/firmarvbm/<int:pk>', DocumentoAnexoFirmarVBM.as_view(),
         name="documento_anexo_firmarvbm"),
    path('documento/detalle/anexo/firmarvbm/bajar/<str:codigo>', DocumentoAnexoFirmarVBMBajar.as_view(),
         name="documento_anexo_firmarvbm_bajar"),
    path('documento/detalle/anexo/firmarvbm/subir/<str:codigo>', DocumentoAnexoFirmarVBMSubir.as_view(),
         name="documento_anexo_firmarvbm_subir"),
    path('documento/detalle/anexo/firmarvbm/error/<str:codigo>', DocumentoAnexoFirmarVBMError.as_view(),
         name="documento_anexo_firmarvbm_error"),

    # Documento - Cargo Recepción Física
    path('documento/recfis/doc/<int:doc>/<int:des>', DocumentoRecFisDoc.as_view(), name="documento_recfis_doc"),

    # Listas personalizadas
    path('combo/dp/listar', DocumentoReferenciaDepListar.as_view(), name="documento_ref_dep_listar"),
    path('combo/uo/listar', DocumentoDestinoUOListar.as_view(), name="documento_destino_uo_listar"),
    path('combo/pt/listar', DocumentoDestinoPTListar.as_view(), name="documento_destino_pt_listar"),
    path('combo/rp/listar', DocumentoResponsableListar.as_view(), name="documento_responsable_listar"),
    path('combo/dt/listar', DocumentoTipoListar.as_view(), name="documento_tipo_listar"),

    # Firmar Documentos
    path('documento/firmar', DocumentoEmitirFirmar.as_view(), name="documento_firmar"),

    # Visar Documentos
    path('documento/visar', DocumentoVisar.as_view(), name="documento_visar"),

    # Bandejas
    path('bandeja/oficina/', include("apps.tramite.urlsbandejaoficina"), name="bandejaoficina"),
    path('bandeja/personal/', include("apps.tramite.urlsbandejapersonal"), name="bandejapersonal"),
    path('bandeja/mesapartes/', include("apps.tramite.urlsbandejamesapartes"), name="bandejamesapartes"),

    # Plantillas - Solo de Forma Temporal
    path('plantillas/', include("apps.tramite.urlsplantillas"), name="plantillas"),

    # Servicios
    path('servicio/', include("apps.tramite.urlsservicio"), name="servicios"),

    # Seguimiento
    path('seguimiento/', include("apps.tramite.urlsseguimiento"), name="seguimiento"),

    # Correlativos
    path('correlativo', CorrelativoVista.as_view(), name="correlativo_inicio"),
    path('correlativo/listar/<int:pk>', CorrelativoListar.as_view(), name="correlativo_listar"),
    path('correlativo/cambiar/<int:pk>', CorrelativoCambiar.as_view(), name="correlativo_cambiar"),

    path('misencargaturas', MisEncargaturas.as_view(), name="misencargaturas_inicio"),
    path('misencargaturas/listar/<int:pt>', MisEncargaturasListar.as_view(), name="misencargaturas_listar"),

]
