"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime
from html import escape

from django.urls import reverse

from apps.tramite.models import Documento, Destino
from apps.tramite.tablas._campos import ColumnaBandejaSeguimiento, ColumnaExpediente, ColumnaDocumento, ColumnaAsunto
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaObs(Columna):
    def render(self, obj):
        _result = super(ColumnaObs, self).render(obj)
        if _result:
            usuario = obj.ultimoestadomensajeria.creador
            if hasattr(usuario, "persona"):
                usuario = '<span title="%s" rel="tooltip">%s</span>' % (
                    usuario.persona.apellidocompleto,
                    usuario.persona.alias
                )
            else:
                usuario = usuario.username
            _result = '<div class="text-info bg-light-info py-1 px-2 rounded strong"><strong>%s: </strong>%s</span>' % (
                usuario,
                _result
            )
        return escape(_result)


class ColumnaAccion(Columna):
    def __init__(self, *args, **kwargs):
        super(ColumnaAccion, self).__init__(
            field="expedientenro", sortable=False, searchable=False, position="center", header=""
        )

    def render(self, obj):
        _result = ""
        if obj.ultimoestadomensajeria.estado in ["DM", "DA"]:
            _result = "<a class='btn btn-icon btn-light-success btn-circle btn-xs' title='Acciones' " \
                      "rel='tooltip' href='%s' data-toggle='modal' data-target='#modal-principal-centro'>" \
                      "<i class='far fa-edit'></i></a>"
            _result = _result % reverse(viewname="apptra:mesapartes_mimensajeria_acciones", kwargs={"pk": obj.pk})
        else:
            contenidohtml = obj.ultimoestadomensajeria.get_estado_display()
            if obj.detallemensajeria:
                contenidohtml += "<br>En Planillado N° %s" % (
                    obj.detallemensajeria.cargoexterno.NumeroFull()
                )
            _result = "<i class='%s text-%s' data-html='true' title='%s' data-toggle='popover' data-content='%s'></i>"
            reenviar = obj.ultimoestadomensajeria.estado in ["EC", "ED", "FD"]
            _result = _result % (
                obj.ultimoestadomensajeria.destino.mensajeriamodoentrega.icono,
                "white" if reenviar else obj.ultimoestadomensajeria.destino.mensajeriamodoentrega.color,
                obj.ultimoestadomensajeria.destino.mensajeriamodoentrega.nombre,
                contenidohtml
            )
            if reenviar:
                _reenvio = "<a href='%s' data-toggle='modal' data-target='#modal-principal-centro' " \
                          "class='btn btn-%s btn-xs btn-icon'>%s</a>"
                _result = _reenvio % (
                    reverse("apptra:mesapartes_mimensajeria_acciones", kwargs={"pk": obj.pk}),
                    obj.ultimoestadomensajeria.destino.mensajeriamodoentrega.color,
                    _result
                )
        return _result


class TablaMesaPartesMiMensajeria(Table):
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="msg")
    documento = ColumnaDocumento(field="documentonrosiglas")
    asunto = ColumnaAsunto(field="documento.asunto")
    destino = Columna(field="destinatario", header="Destino", sortable=False, searchable=False)
    folios = Columna(field="documento.folios", header="Folios", position="center")
    observacion = ColumnaObs(field="ultimoestadomensajeria.observacion", header="Observación")
    fecha = ColumnaFecha(field="ultimoestadomensajeria.creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    estado = Columna(field="ultimoestadomensajeriae", visible=False, searchable=False)
    accion = ColumnaAccion()

    class Meta:
        model = Destino
        id = "tablaMesaPartesMiMensajeria"
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
                "id": "btnAcc",
                "icono": "fa fa-plus",
                "texto": "Acciones",
                "modal": "#modal-principal-centro",
                "url": "",
                "attrs": {
                    "data-modal-size": "md"
                }
            }
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaMesaPartesMiMensajeria, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:mesapartes_mimensajeria_listar")
