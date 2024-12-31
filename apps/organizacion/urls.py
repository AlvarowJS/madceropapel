"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.organizacion.vistas.apoyo import ApoyoInicio, ApoyoListar, ApoyoAgregar, ApoyoEditar, ApoyoAutorizar, \
    ApoyoEliminar
from apps.organizacion.vistas.area import AreaInicio, AreaListar, AreaAgregar, AreaEditar, AreaEliminar, AreaActivar, \
    AreaMover, AreaDetalle
from apps.organizacion.vistas.comision import ComisionInicio, ComisionListar, ComisionAgregar, ComisionEditar, \
    ComisionEliminar, ComisionAutorizarGenerar, ComisionAutorizarBajar, ComisionAutorizarSubir, ComisionAutorizarError, \
    ComisionDirectaAgregar, ComisionDirectaListar, ComisionDirectaEditar, ComisionDirectaEliminar, ComisionApoyoListar, \
    ComisionApoyoAgregar, ComisionApoyoEditar, ComisionApoyoEliminar
from apps.organizacion.vistas.comisionsolicitudes import ComisionSolicitudesListar, ComisionSolicitudesAprobar, \
    ComisionSolicitudesAnular
from apps.organizacion.vistas.dependencia import DependenciaInicio, DependenciaGuardar
from apps.organizacion.vistas.documentotipoarea import DocumentoTipoAreaInicio, DocumentoTipoAreaAgregar, \
    DocumentoTipoAreaEliminar, DocumentoTipoAreaListar, DocumentoTipoAreaAreasListar
from apps.organizacion.vistas.encargatura import EncargaturaInicio, EncargaturaListar, EncargaturaAgregar, \
    EncargaturaFirmar, EncargaturaFirmarBajar, EncargaturaFirmarSubir, EncargaturaFirmarError, EncargaturaAnular, \
    EncargaturaAnularBajar, EncargaturaAnularSubir, EncargaturaAnularError, EncargaturaEliminar, EncargaturaEditar, \
    EncargaturaPuestoListar, EncargaturaPuestoAgregar, EncargaturaPuestoTerminar, EncargaturaCargoDoc, \
    EncargaturaCargoDocAnu
from apps.organizacion.vistas.integrante import IntegranteListar, IntegranteAgregar, IntegranteEditar, IntegranteQuitar, \
    IntegranteCambiar, IntegranteDirectaListar, IntegranteDirectaAgregar, IntegranteDirectaEditar, \
    IntegranteDirectaQuitar
from apps.organizacion.vistas.proyeccion import ProyeccionInicio, ProyeccionListar, ProyeccionAgregar, \
    ProyeccionEliminar, ProyeccionAreaListar, ProyeccionAreaEliminar, ProyeccionAreaAgregar
from apps.organizacion.vistas.trabajador import TrabajadorInicio, TrabajadorListar, TrabajadorAgregar, \
    TrabajadorEditar, TrabajadorEliminar, TrabajadorPassword, TrabajadorAreaListar, TrabajadorRotar, TrabajadorLogout, \
    TrabajadorBaja

app_name = "apporg"

urlpatterns = [
    path('dependencia', DependenciaInicio.as_view(), name="dependencia_inicio"),
    path('dependencia/guardar', DependenciaGuardar.as_view(), name="dependencia_guardar"),

    path('area', AreaInicio.as_view(), name="area_inicio"),
    path('area/listar', AreaListar.as_view(), name="area_listar"),
    path('area/<int:padre>/agregar', AreaAgregar.as_view(), name="area_agregar"),
    path('area/<int:pk>/editar', AreaEditar.as_view(), name="area_editar"),
    path('area/<int:pk>/eliminar', AreaEliminar.as_view(), name="area_eliminar"),
    path('area/<int:pk>/activar', AreaActivar.as_view(), name="area_activar"),
    path('area/<int:pk>/mover', AreaMover.as_view(), name="area_mover"),
    path('area/<int:pk>/detalle', AreaDetalle.as_view(), name="area_detalle"),

    path('documentotipoarea', DocumentoTipoAreaInicio.as_view(), name="documentotipoarea_inicio"),
    path('documentotipoarea/areas/listar', DocumentoTipoAreaAreasListar.as_view(),
         name="documentotipoarea_areas_listar"),
    path('documentotipoarea/listar/<int:area>', DocumentoTipoAreaListar.as_view(), name="documentotipoarea_listar"),
    path('documentotipoarea/agregar/<int:area>', DocumentoTipoAreaAgregar.as_view(), name="documentotipoarea_agregar"),
    path('documentotipoarea/eliminar/<int:pk>', DocumentoTipoAreaEliminar.as_view(), name="documentotipoarea_eliminar"),

    # Trabajadores
    path('trabajador', TrabajadorInicio.as_view(), name="trabajador_inicio"),
    path('trabajador/area/listar', TrabajadorAreaListar.as_view(), name="trabajador_area_listar"),
    path('trabajador/listar/<int:area>/<int:todos>', TrabajadorListar.as_view(), name="trabajador_listar"),
    path('trabajador/<int:area>/agregar', TrabajadorAgregar.as_view(), name="trabajador_agregar"),
    path('trabajador/<int:pk>/editar', TrabajadorEditar.as_view(), name="trabajador_editar"),
    path('trabajador/<int:pk>/eliminar', TrabajadorEliminar.as_view(), name="trabajador_eliminar"),
    path('trabajador/<int:pk>/password', TrabajadorPassword.as_view(), name="trabajador_password"),
    path('trabajador/<int:pk>/logout', TrabajadorLogout.as_view(), name="trabajador_logout"),
    path('trabajador/<int:pk>/rotar', TrabajadorRotar.as_view(), name="trabajador_rotar"),
    path('trabajador/<int:pk>/baja', TrabajadorBaja.as_view(), name="trabajador_baja"),

    path('proyeccion', ProyeccionInicio.as_view(), name="proyeccion_inicio"),
    path('proyeccion/<int:pt>/listar', ProyeccionListar.as_view(), name="proyeccion_listar"),
    path('proyeccion/<int:pt>/agregar', ProyeccionAgregar.as_view(), name="proyeccion_agregar"),
    path('proyeccion/<int:pk>/eliminar', ProyeccionEliminar.as_view(), name="proyeccion_eliminar"),
    path('proyeccion/area/listar', ProyeccionAreaListar.as_view(), name="proyeccionarea_listar"),
    path('proyeccion/area/<int:pk>/eliminar', ProyeccionAreaEliminar.as_view(), name="proyeccionarea_eliminar"),
    path('proyeccion/area/agregar', ProyeccionAreaAgregar.as_view(), name="proyeccionarea_agregar"),

    path('comision', ComisionInicio.as_view(), name="comision_inicio"),
    path('comision/listar', ComisionListar.as_view(), name="comision_listar"),
    path('comision/agregar', ComisionAgregar.as_view(), name="comision_agregar"),
    path('comision/editar/<int:pk>', ComisionEditar.as_view(), name="comision_editar"),
    path('comision/eliminar/<int:pk>', ComisionEliminar.as_view(), name="comision_eliminar"),
    path('comision/autorizar/<int:pk>/generar', ComisionAutorizarGenerar.as_view(), name="comision_autorizar_generar"),
    path('comision/autorizar/<int:pk>/bajar', ComisionAutorizarBajar.as_view(), name="comision_autorizar_bajar"),
    path('comision/autorizar/<int:pk>/subir', ComisionAutorizarSubir.as_view(), name="comision_autorizar_subir"),
    path('comision/autorizar/<int:pk>/error', ComisionAutorizarError.as_view(), name="comision_autorizar_error"),
    path('comision/apoyo/<int:pk>/listar', ComisionApoyoListar.as_view(), name="comision_apoyo_listar"),
    path('comision/apoyo/<int:pk>/agregar', ComisionApoyoAgregar.as_view(), name="comision_apoyo_agregar"),
    path('comision/apoyo/<int:pk>/editar', ComisionApoyoEditar.as_view(), name="comision_apoyo_editar"),
    path('comision/apoyo/<int:pk>/eliminar', ComisionApoyoEliminar.as_view(), name="comision_apoyo_eliminar"),
    path('integrante/<int:comid>/listar', IntegranteListar.as_view(), name="integrante_listar"),
    path('integrante/<int:comid>/agregar', IntegranteAgregar.as_view(), name="integrante_agregar"),
    path('integrante/<int:pk>/editar', IntegranteEditar.as_view(), name="integrante_editar"),
    path('integrante/<int:pk>/quitar', IntegranteQuitar.as_view(), name="integrante_quitar"),
    path('integrante/<int:pk>/cambiar', IntegranteCambiar.as_view(), name="integrante_cambiar"),

    path('comisiond/listar', ComisionDirectaListar.as_view(), name="comisiondirecta_listar"),
    path('comisiond/agregar', ComisionDirectaAgregar.as_view(), name="comisiondirecta_agregar"),
    path('comisiond/editar/<int:pk>', ComisionDirectaEditar.as_view(), name="comisiondirecta_editar"),
    path('comisiond/eliminar/<int:pk>', ComisionDirectaEliminar.as_view(), name="comisiondirecta_eliminar"),

    path('integranted/<int:comid>/listar', IntegranteDirectaListar.as_view(), name="integrantedirecta_listar"),
    path('integranted/<int:comid>/agregar', IntegranteDirectaAgregar.as_view(), name="integrantedirecta_agregar"),
    path('integranted/<int:pk>/editar', IntegranteDirectaEditar.as_view(), name="integrantedirecta_editar"),
    path('integranted/<int:pk>/quitar', IntegranteDirectaQuitar.as_view(), name="integrantedirecta_quitar"),

    # SOLICITUDES DE COMISION
    path('comisionsolicitudes/listar', ComisionSolicitudesListar.as_view(), name="comisionsolicitudes_listar"),
    path('comisionsolicitudes/aprobar/<int:pk>', ComisionSolicitudesAprobar.as_view(),
         name="comisionsolicitudes_aprobar"),
    path('comisionsolicitudes/anular/<int:pk>', ComisionSolicitudesAnular.as_view(),
         name="comisionsolicitudes_anular"),

    # Encargaturas
    path('encargatura', EncargaturaInicio.as_view(), name="encargatura_inicio"),
    path('encargatura/listar', EncargaturaListar.as_view(), name="encargatura_listar"),
    path('encargatura/agregar', EncargaturaAgregar.as_view(), name="encargatura_agregar"),
    path('encargatura/editar/<int:pk>', EncargaturaEditar.as_view(), name="encargatura_editar"),
    path('encargatura/firmar/<int:pk>', EncargaturaFirmar.as_view(), name="encargatura_firmar"),
    path('encargatura/firmar/bajar/<int:pk>/<int:ptid>', EncargaturaFirmarBajar.as_view(),
         name="encargatura_firmar_bajar"),
    path('encargatura/firmar/subir/<int:pk>', EncargaturaFirmarSubir.as_view(), name="encargatura_firmar_subir"),
    path('encargatura/firmar/error/<int:pk>', EncargaturaFirmarError.as_view(), name="encargatura_firmar_error"),
    path('encargatura/anular/<int:pk>', EncargaturaAnular.as_view(), name="encargatura_anular"),
    path('encargatura/anular/bajar/<int:pk>/<int:ptid>', EncargaturaAnularBajar.as_view(),
         name="encargatura_anular_bajar"),
    path('encargatura/anular/subir/<int:pk>', EncargaturaAnularSubir.as_view(), name="encargatura_anular_subir"),
    path('encargatura/anular/error/<int:pk>', EncargaturaAnularError.as_view(), name="encargatura_anular_error"),
    path('encargatura/eliminar/<int:pk>', EncargaturaEliminar.as_view(), name="encargatura_eliminar"),
    path('encargatura/cargo/doc/<int:pk>', EncargaturaCargoDoc.as_view(), name="encargatura_cargo_doc"),
    path('encargatura/cargo/docanu/<int:pk>', EncargaturaCargoDocAnu.as_view(), name="encargatura_cargo_docanu"),

    # Encargaturas por Puesto
    path('encargaturapuesto/listar', EncargaturaPuestoListar.as_view(), name="encargaturapuesto_listar"),
    path('encargaturapuesto/agregar', EncargaturaPuestoAgregar.as_view(), name="encargaturapuesto_agregar"),
    path('encargaturapuesto/terminar/<int:pk>', EncargaturaPuestoTerminar.as_view(), name="encargaturapuesto_terminar"),

    # Apoyos
    path('apoyo', ApoyoInicio.as_view(), name="apoyo_inicio"),
    path('apoyo/listar', ApoyoListar.as_view(), name="apoyo_listar"),
    path('apoyo/agregar', ApoyoAgregar.as_view(), name="apoyo_agregar"),
    path('apoyo/editar/<int:pk>', ApoyoEditar.as_view(), name="apoyo_editar"),
    path('apoyo/autorizar/<int:pk>', ApoyoAutorizar.as_view(), name="apoyo_autorizar"),
    # path('apoyo/firmar/bajar/<int:pk>', ApoyoFirmarBajar.as_view(), name="apoyo_firmar_bajar"),
    # path('apoyo/firmar/subir/<int:pk>', ApoyoFirmarSubir.as_view(), name="apoyo_firmar_subir"),
    # path('apoyo/firmar/error/<int:pk>', ApoyoFirmarError.as_view(), name="apoyo_firmar_error"),
    # path('apoyo/anular/<int:pk>', ApoyoAnular.as_view(), name="apoyo_anular"),
    # path('apoyo/anular/bajar/<int:pk>', ApoyoAnularBajar.as_view(), name="apoyo_anular_bajar"),
    # path('apoyo/anular/subir/<int:pk>', ApoyoAnularSubir.as_view(), name="apoyo_anular_subir"),
    # path('apoyo/anular/error/<int:pk>', ApoyoAnularError.as_view(), name="apoyo_anular_error"),
    path('apoyo/eliminar/<int:pk>', ApoyoEliminar.as_view(), name="apoyo_eliminar"),

]
