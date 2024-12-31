"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime
from html import escape

from django.urls import reverse

from apps.tramite.models import Destino
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaBandejaSeguimiento, ColumnaAsunto, \
    ColumnaDestinoEstado, ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaEntregaFisica(Columna):
    def __init__(self, field, *args, **kwargs):
        super(ColumnaEntregaFisica, self).__init__(
            field=field, searchable=False, sortable=False, header="", position="center"
        )

    def render(self, obj):
        _result = ""
        if obj.entregafisica:
            _result = "<i class='flaticon-file-1' rel='tooltip' data-html='true' title='%s'></i>"
            _result = _result % obj.entregafisica
        return escape(_result)


class TablaOficinaEntrada(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEntrada")
    fecha = ColumnaFecha(field="destinoemision", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonrosiglas")
    asunto = ColumnaAsunto("documento.asunto")
    remitente = Columna(field="remitente", header="Remitente")
    entregafisica = ColumnaEntregaFisica(field="entregafisica")
    estado = ColumnaDestinoEstado()

    class Meta:
        model = Destino
        id = "tabladbEntradaO"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "destinoemision"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }
        selectrowcheckbox = True
        toolbar = [
            {
                "id": "btnRecepcionar",
                "icono": "fas fa-arrow-down fa-1x",
                "class": "btn-shadow",
                "texto": "Recepcionar",
                "url": "#",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaOficinaEntrada, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:oficina_bandeja_entrada_listar")
