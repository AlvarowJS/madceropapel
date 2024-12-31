"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.conf import settings
from django.template.defaultfilters import pluralize
from django.urls import reverse, reverse_lazy
from django.utils.html import escape

from apps.tramite.models import Documento
from apps.tramite.tablas._campos import ColumnaDocumento, ColumnaAsunto, ColumnaBandejaSeguimiento, ColumnaExpediente
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha
from modulos.datatable.utils import Accessor


class ColumnaDocumentoValida(ColumnaDocumento):
    def __init__(self, field):
        super(ColumnaDocumentoValida, self).__init__(field, modo=2, vermodo=False)

    def render(self, obj):
        if obj.documentoplantilla.contenido:
            _result = super(ColumnaDocumentoValida, self).render(obj)
        else:
            _result = obj.documentonrosiglas
        if obj.origentipo == "V":
            modo = "<span class='label label-sm mr-1 label-light-warning' rel='tooltip' " + \
                   "title='%s'>%s</span>"
            modo = escape(modo % (obj.get_origentipo_display(), obj.origentipo))
            _result = "%s %s" % (
                modo,
                _result
            )
        return _result


class ColumnaDestino(Columna):
    def render(self, obj):
        _result = super(ColumnaDestino, self).render(obj)
        _rutaedicion = reverse(viewname="apptra:mesapartes_registrar_destinos", kwargs={"pk": obj.pk})
        if obj.des_documento.exclude(ultimoestado__estado="AN").count() == 0:
            _result = "<div class='text-center'>" \
                      "<a class='btn btn-xs btn-icon btn-light-primary' data-modal-size='xl' " \
                      "href='%s' data-toggle='modal' data-target='#modal-principal-centro' " \
                      "rel='tooltip' title='Agregar Destinos'>" \
                      "<i class='fas fa-plus-circle'></i></a></div>"
            _result = _result % _rutaedicion
        else:
            # if obj.ultimoestado.estado != "EM":
            _ruta = "<a href='%s' data-toggle='modal' data-modal-size='xl' " \
                    "data-target='#modal-principal-centro'>%s</a>"
            _result = escape(_ruta % (
                _rutaedicion,
                Accessor(self.field).resolve(obj)
            ))
        return _result


class ColumnaPdf(Columna):
    def __init__(self):
        super(ColumnaPdf, self).__init__(
            field="expedientenro",
            position="center",
            header_attrs={"class": "text-center nowrap"},
            header="Archivos",
            sortable=False,
            searchable=False
        )

    def render(self, obj):
        _result = ""
        if not obj.ultimoestado.estado in ["EM", "RP", "RT", "AT", "AR"]:
            _result = '<a href="%s" class="btn btn-xs btn-light-%s btn-icon" rel="tooltip" ' \
                      'title="%s" data-toggle="modal" data-target="#modal-principal-centro" data-modal-size="lg">' \
                      '<i class="%s"></i>' \
                      '</a>'
            urlfile = reverse(viewname="apptra:mesapartes_registrar_archivos", kwargs={"pk": obj.pk})
            if (not obj.documentotipoarea.documentotipo.esmultiple and obj.documentoplantilla.contenido) or \
                    (obj.documentotipoarea.documentotipo.esmultiple and obj.TramiteDocumentosCargados() > 0):
                _result = _result % (
                    urlfile,
                    "success",
                    "Cambiar Archivo" + ("s" if obj.documentotipoarea.documentotipo.esmultiple else ""),
                    "fas fa-pen",
                )
            else:
                if obj.documentotipoarea.documentotipo.esmultiple and \
                        obj.des_documento.exclude(ultimoestado__estado="AN").count() == 0:
                    _result = ""
                else:
                    _result = _result % (
                        urlfile,
                        "primary",
                        "Agregar Archivo" + ("s" if obj.documentotipoarea.documentotipo.esmultiple else ""),
                        "fas fa-plus-circle"
                    )
            _anexos = '<a href="%s" class="btn btn-light-primary btn-icon btn-xs ml-1 w-30px" rel="tooltip" ' \
                      'title="%s" data-toggle="modal" data-target="#modal-principal-centro" data-modal-size="lg">' \
                      '<i class="fa font-size-sm fas fa-paperclip"></i>' \
                      '<span class="ml-2 font-weight-bold">%s</span>' \
                      '</a>'
            urlanx = reverse(viewname="apptra:mesapartes_registrar_anexos", kwargs={"pk": obj.pk})
            _anexos = _anexos % (
                urlanx, "Registro de Anexos",
                obj.anexos.count()
            )
            _result += _anexos
        return _result


class ColumnaEmitir(Columna):
    def __init__(self):
        super(ColumnaEmitir, self).__init__(
            field="expedientenro",
            position="center",
            header_attrs={"class": "text-center nowrap w-95px"},
            header="",
            sortable=False,
            searchable=False
        )

    def render(self, obj):
        _result = ""
        if not obj.ultimoestado.estado in ["EM", "RP", "RT", "AT", "AR"]:
            if (not obj.documentotipoarea.documentotipo.esmultiple and
                obj.des_documento.exclude(ultimoestado__estado="AN").count() > 0 and
                obj.documentoplantilla.contenido) or \
                    (obj.documentotipoarea.documentotipo.esmultiple and
                     obj.des_documento.exclude(ultimoestado__estado="AN").count() > 0 and
                     obj.TramiteDocumentosFaltantes() == 0):
                _emision = '<a href="%s" class="btn btn-xs btn-light-warning btn-icon mr-2" ' \
                           'rel="tooltip" title="Emitir" data-toggle="modal" ' \
                           'data-target="#modal-principal-centro">' \
                           '<i class="fas fa-paper-plane fa-1x"></i>' \
                           '</a>'
                _result += _emision % reverse(viewname="apptra:mesapartes_registrar_emitir", kwargs={"pk": obj.pk})
        printTK = '<a class="btn btn-xs btn-light-info btn-icon" rel="tooltip" title="Imprimir Ticket" ' + \
                  'onclick="imprimirTicket(%s, %s);">' + \
                  '<i class="flaticon2-print"></i>' + \
                  '</a>'
        _result += printTK % (obj.pk, settings.CONFIG_APP["MPTicketAlto"])
        if obj.ultimoestado.estado in ["EM"] and obj.estadoemitido and obj.emisor.pk == obj.periodoactualid:
            btmAnular = '<a class="btn btn-xs btn-light-warning btn-icon ml-2" rel="tooltip" ' + \
                        'title="Anular Emisión" ' + \
                        'href="%s" data-toggle="modal" data-target="#modal-principal-centro">' + \
                        '<i class="fas fa-undo"></i>' + \
                        '</a>'
            _result += btmAnular % reverse(viewname="apptra:mesapartes_registrar_emitir_anular", kwargs={"pk": obj.pk})
        if not obj.ultimoestado.estado in ["EM", "RP", "RT", "AT", "AR"]:
            btmELiminar = '<a class="btn btn-xs btn-light-danger btn-icon ml-2" rel="tooltip" ' + \
                          'title="Eliminar Expediente" ' + \
                          'href="%s" data-toggle="modal" data-target="#modal-principal-centro">' + \
                          '<i class="fas fa-trash-alt"></i>' + \
                          '</a>'
            _result += btmELiminar % reverse(viewname="apptra:mesapartes_registrar_eliminar", kwargs={"pk": obj.pk})
        return _result


class ColumnaArchivos(Columna):
    def render(self, obj):
        _result = False
        if (not obj.documentotipoarea.documentotipo.esmultiple and obj.documentoplantilla.contenido) or \
                (obj.documentotipoarea.documentotipo.esmultiple and obj.TramiteDocumentosCargados() > 0):
            _result = not _result
        return _result


class TablaMesaPartesRegistrados(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbMesaRegistrados", openin="TD")
    fecha = ColumnaFecha(field="ultimoestado.creado", header="Exp Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumentoValida(field="documentonrosiglas")
    asunto = ColumnaAsunto(field="asunto")
    remitente = Columna(field="remitente", header="Remitente")
    destino = ColumnaDestino(field="ListaDestinosBandeja", header="Destino", searchable=False, sortable=False)
    pdf = ColumnaPdf()
    creador = Columna(field="creador.persona.alias", header="Creador", position="center")
    emisor = Columna(field="editor.persona.alias", header="Emisor", position="center")
    creadorfull = Columna(field="creador.persona.apellidocompleto", visible=False)
    emitir = ColumnaEmitir()
    tienearchivos = ColumnaArchivos(field="expedientenro", visible=False)

    class Meta:
        model = Documento
        id = "tablaMesaPartesRegistrados"
        selectrowcheckbox = True
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "ultimoestado.creado"
        }
        filter_tipodoc = {
            "field": "documentotipoarea.documentotipo"
        }
        toolbar = [
            # {
            #     "id": "btnSubirEscaneados",
            #     "icono": "fas fa-file-pdf fa-1x",
            #     "clase": "btn-shadow btn-primary",
            #     "texto": "Subir Escaneados",
            #     # "modal": "#modal-principal-centro",
            #     "url": "#",
            #     "attrs": {
            #         "data-modal-size": "md",
            #         "campo": "1"
            #     }
            # },
            {
                "id": "btnEmitirMasivo",
                "icono": "fas fa-paper-plane fa-1x",
                "clase": "btn-shadow btn-primary",
                "texto": "Emitir Masivo",
                "modal": "#modal-centro-scroll",
                "url": reverse_lazy("apptra:mesapartes_bandeja_registrados_emisionmasiva"),
                "attrs": {
                    "data-modal-size": "md",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaMesaPartesRegistrados, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(
            viewname="apptra:mesapartes_bandeja_registrados_listar",
            kwargs={
                "modo": "P",
                "users": "_0"
            }
        )
