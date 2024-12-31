"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime
from html import escape

from django.urls import reverse, reverse_lazy

from apps.tramite.models import Destino, CargoExternoDetalle, CargoExterno
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaBandejaSeguimiento
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha, ColumnaAcciones
from modulos.datatable.utils import Accessor


class ColumnaAccionesPE(Columna):
    def __init__(self):
        super(ColumnaAccionesPE, self).__init__(
            field="pk",
            position="center",
            header_attrs={"class": "text-center nowrap w-95px"},
            header="",
            sortable=False,
            searchable=False
        )

    def render(self, obj):
        _result = ""
        if obj.ultimoestadomensajeria.estado == "PE":
            btnRecibir = '<a class="btn btn-xs btn-light-primary btn-icon mx-1" rel="tooltip" title="Recibir" ' + \
                         'href="%s" data-toggle="modal" data-target="#modal-principal-centro" data-modal-size="lg">' + \
                         '<i class="fas fa-check"></i>' + \
                         '</a>'
            _result += btnRecibir % reverse(
                viewname="apptra:mesapartes_mensajeria_recibir",
                kwargs={"ids": "%s_" % obj.pk}
            )

            btnDevolver = '<a class="btn btn-xs btn-light-warning btn-icon mx-1" rel="tooltip" title="Devolver" ' + \
                          'data-toggle="modal" data-target="#modal-principal-centro" data-modal-size="lg" ' + \
                          'href="%s">' + \
                          '<i class="fas fa-undo"></i>' + \
                          '</a>'

            _result += btnDevolver % reverse(
                viewname="apptra:mesapartes_mensajeria_devolver",
                kwargs={"ids": "%s_" % obj.pk}
            )

            btnEnviado = '<a class="btn btn-xs btn-light-success btn-icon mx-1" rel="tooltip" ' \
                         'title="Finalizado Directo" href="%s" data-toggle="modal" ' + \
                         'data-target="#modal-principal-centro" data-modal-size="lg">' + \
                         '<i class="fas fa-check-double"></i>' + \
                         '</a>'
            btnEnviado = btnEnviado % (
                reverse(viewname="apptra:mesapartes_mensajeria_finalizar_directo", kwargs={"desid": obj.pk})
            )

            _result += btnEnviado
        else:
            _result += '<span class="label label-outline-danger label-inline" rel="tooltip" title="%s">%s</span>'
            _result = _result % (
                obj.ultimoestadomensajeria.observacion,
                "Observado"  # obj.ultimoestadomensajeria.get_estado_display()
            )
        return _result


class ColumnaAccionesXE(Columna):
    def __init__(self):
        super(ColumnaAccionesXE, self).__init__(
            field="pk",
            position="center",
            header_attrs={"class": "text-center nowrap w-95px"},
            header="",
            sortable=False,
            searchable=False
        )

    def render(self, obj):
        _result = ""
        btnDevolver = '<a class="btn btn-xs btn-light-warning btn-icon mx-1" rel="tooltip" title="Devolver" ' + \
                      'onclick="devolver();">' + \
                      '<i class="fas fa-undo"></i>' + \
                      '</a>'
        _result += btnDevolver
        if obj.mesapartesmodoenvio == 2:
            btnImprimir = '<a class="btn btn-xs btn%s-info btn-icon mx-1" rel="tooltip" title="Imprimir" ' + \
                          'href="%s" data-toggle="modal" data-target="#modal-principal-centro" ' \
                          'data-modal-size="lg" data-btnid="%s">' + \
                          '<i class="flaticon2-print"></i>' + \
                          '</a>'
            _color = "" if obj.LRevisiones().filter(impreso=True).count() == 0 else "-light"
            _result += btnImprimir % (
                _color,
                reverse(viewname="apptra:mesapartes_mensajeria_imprimir", kwargs={"pk": obj.pk}),
                obj.pk
            )

        btnEnviado = '<a class="btn btn-xs btn-light-success btn-icon mx-1" rel="tooltip" ' \
                     'title="Finalizado Directo" href="%s" data-toggle="modal" ' + \
                     'data-target="#modal-principal-centro" data-modal-size="lg">' + \
                     '<i class="fas fa-check-double"></i>' + \
                     '</a>'
        btnEnviado = btnEnviado % (
            reverse(viewname="apptra:mesapartes_mensajeria_finalizar_directo", kwargs={"desid": obj.pk})
        )

        _result += btnEnviado

        return _result


class ColumnaPlanillado(Columna):
    def render(self, obj):
        return "%s" % obj.cargoexterno.NumeroFull()


class ColumnaAccionesPL(Columna):
    def __init__(self):
        super(ColumnaAccionesPL, self).__init__(
            field="pk",
            position="center",
            header_attrs={"class": "text-center nowrap w-95px"},
            header="",
            sortable=False,
            searchable=False
        )

    def render(self, obj):
        _result = ""

        return _result


class ColumnaEstadoPL(Columna):
    def render(self, obj):
        _result = "<i class='%s text-%s' rel='tooltip' title='%s' data-html='true'></i>"
        if obj.estado == "PE":
            _result = _result % ("fas fa-question-circle", "warning", obj.get_estado_display())
            if obj.cargoexterno.ultimoestado.estado == "GN":
                _result += "<a href='%s' data-toggle='modal' data-target='#modal-principal-centro' " + \
                           "class='btn btn-primary btn-icon btn-xs ml-2' " + \
                           "title='Editar' rel='tooltip'>" + \
                           "<i class='far fa-edit'></i></a>"
                _result = _result % reverse(viewname="apptra:mesapartes_planillado_rectificar", kwargs={"pk": obj.pk})
        elif obj.estado == "ET":
            _result = _result % ("far fa-check-circle", "success", obj.get_estado_display())
        elif obj.estado == "RE":
            _result = _result % ("far fa-times-circle", "danger", '%s:<br/><span class="text-danger">%s</span>' % (
                obj.get_estado_display(), obj.cargocomentario
            ))
        else:
            _result = ""
        return escape(_result)


class ColumnaFechaObsFI(ColumnaFecha):
    def __init__(self, field):
        super(ColumnaFechaObsFI, self).__init__(
            field=field, header="Fecha", format="%d/%m/%Y %I:%M %p"
        )

    def render(self, obj):
        _result = super(ColumnaFechaObsFI, self).render(obj)
        _result = "<div class='bg-light-warning px-2 py-1 rounded' title='%s' rel='tooltip'>%s</span>" % (
            obj.ultimoestadomensajeria.observacion,
            _result
        )
        return _result


class TablaMensajeriaPE(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="msg")
    documento = ColumnaDocumento(field="documentonrosiglas")
    folios = Columna(field="documento.folios", header="Folios")
    remitente = Columna(field="remitente", header="Remitente")
    destino = Columna(field="destinatario", header="Destino")
    direccion = Columna(field="direccion", header="Dirección")
    ubigeo = Columna(field="ubigeofull", header="Ubigeo")
    fecha = ColumnaFecha(field="ultimoestadomensajeria.creado", header="Derivado", format="%d/%m/%Y %I:%M %p")
    acciones = ColumnaAccionesPE()

    class Meta:
        model = Destino
        id = "tablaMensajeriaPE"
        selectrowcheckbox = True
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "ultimoestadomensajeria.creado"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }
        toolbar = [
            {
                "id": "btnRecibirMasivo",
                "icono": "fas fa-check fa-1x",
                "clase": "btn-shadow btn-primary",
                "texto": "Recibir",
                "modal": "#modal-centro-scroll",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            },
            {
                "id": "btnDevolverMasivo",
                "icono": "fas fa-undo fa-1x",
                "clase": "btn-shadow btn-light-warning",
                "texto": "Devolver",
                "modal": "#modal-centro-scroll",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaMensajeriaPE, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:mesapartes_mensajeria_listar", kwargs={
            "id": "PE", "ambito": "T", "padre": 0
        })


class TablaMensajeriaXE(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="mensajeria")
    documento = ColumnaDocumento(field="documentonro")
    remitente = Columna(field="remitente", header="Remitente")
    destino = Columna(field="destinatario", header="Destino")
    direccion = Columna(field="direccion", header="Dirección")
    ubigeo = Columna(field="ubigeofull", header="Ubigeo")
    derivado = ColumnaFecha(field="ultimafechaderivado()", header="Derivado", format="%d/%m/%Y %I:%M %p")
    recibido = ColumnaFecha(field="ultimoestadomensajeria.creado", header="Recibido", format="%d/%m/%Y %I:%M %p")
    acciones = ColumnaAccionesXE()

    class Meta:
        model = Destino
        id = "tablaMensajeriaXE"
        selectrowcheckbox = True
        toolbar = [
            {
                "id": "btnNuevoPlanillado",
                "icono": "far fa-list-alt fa-1x",
                "clase": "btn-shadow btn-primary",
                "texto": "Nuevo Planillado",
                "modal": "#modal-centro-scroll",
                "attrs": {
                    "data-modal-size": "xl",
                    "campo": "1"
                }
            },
            {
                "id": "btnAgregarPlanillado",
                "icono": "fas fa-plus fa-1x",
                "clase": "btn-shadow btn-primary",
                "texto": "Agregar a Planillado",
                "modal": "#modal-centro-scroll",
                "attrs": {
                    "data-modal-size": "xl",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaMensajeriaXE, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:mesapartes_mensajeria_listar", kwargs={
            "id": "XE", "ambito": "T", "padre": 0
        })


class ColumnaCambiada(Columna):
    def __init__(self, field, fieldnew, header):
        super(ColumnaCambiada, self).__init__(field=field, header=header)
        self.fieldnew = fieldnew

    def render(self, obj):
        _result = super(ColumnaCambiada, self).render(obj)
        newdir = Accessor(self.fieldnew).resolve(obj)
        if newdir:
            _result = "<strong>%s</strong>" % newdir
        return escape(_result)


class TablaMensajeriaPL(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    planillado = ColumnaPlanillado(field="cargoexterno.numero", header="Planillado", position="center")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEntrada")
    documento = ColumnaDocumento(field="documentonro")
    destino = Columna(field="destinatario", header="Destino")
    ubigeo = ColumnaCambiada(field="ubigeonombre", fieldnew="ubigeonombrenew", header="Ubigeo")
    direccion = ColumnaCambiada(field="direccionfull", fieldnew="direccionfullnew", header="Dirección")
    detalle = Columna(field="detalle", header="Detalle")
    estado = ColumnaEstadoPL(field="cargoexterno.numero", header="Estado", position="center", sortable=False)

    class Meta:
        model = CargoExternoDetalle
        id = "tablaMensajeriaPL"

    def __init__(self, request, *args, **kwargs):
        super(TablaMensajeriaPL, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:mesapartes_mensajeria_listar", kwargs={
            "id": "PL", "ambito": "X", "padre": 0
        })


class TablaMensajeriaFI(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    planillado = ColumnaPlanillado(field="cargoexterno.numero", header="Planillado", position="center")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEntrada")
    documento = ColumnaDocumento(field="documentonro")
    remitente = Columna(field="remitente", header="Remitente")
    destino = Columna(field="destinatario", header="Destino")
    ubigeo = ColumnaCambiada(field="ubigeonombre", fieldnew="ubigeonombrenew", header="Ubigeo")
    direccion = ColumnaCambiada(field="direccionfull", fieldnew="direccionfullnew", header="Dirección")
    detalle = Columna(field="detalle", header="Detalle")
    estado = ColumnaEstadoPL(field="cargoexterno.numero", header="Estado", position="center", sortable=False)

    class Meta:
        model = CargoExternoDetalle
        id = "tablaMensajeriaFI"

    def __init__(self, request, *args, **kwargs):
        super(TablaMensajeriaFI, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:mesapartes_mensajeria_listar", kwargs={
            "id": "FI", "ambito": "X", "padre": 0
        })


class TablaMensajeriaFD(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="mensajeria")
    documento = ColumnaDocumento(field="documentonro")
    remitente = Columna(field="remitente", header="Remitente")
    destino = Columna(field="destinatario", header="Destino")
    direccion = Columna(field="direccion", header="Dirección")
    ubigeo = Columna(field="ubigeofull", header="Ubigeo")
    fecha = ColumnaFecha(field="ultimoestadomensajeria.fecha", header="Fecha")
    nota = Columna(field="ultimoestadomensajeria.observacion", header="Nota")
    creador = Columna(field="ultimoestadomensajeria.creador.persona.alias", header="Creador")

    class Meta:
        model = Destino
        id = "tablaMensajeriaFD"
        selectrowcheckbox = True

    def __init__(self, request, *args, **kwargs):
        super(TablaMensajeriaFD, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:mesapartes_mensajeria_listar", kwargs={
            "id": "FD", "ambito": "T", "padre": 0
        })
