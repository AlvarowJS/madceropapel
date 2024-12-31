"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import Destino
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaAsunto, ColumnaBandejaSeguimiento, \
    ColumnaDestinoEstado, ColumnaBandejaConfidencial
from apps.tramite.tablas.oficinaentrada import ColumnaEntregaFisica
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaRemitente(Columna):
    def render(self, obj):
        return obj.documento.Remitente()


class TablaPersonalEntrada(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEntrada")
    fecha = ColumnaFecha(field="destinoemision", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonro")
    asunto = ColumnaAsunto(field="documento.asunto")
    remitente = ColumnaRemitente(field="remitente", header="Remitente")
    entregafisica = ColumnaEntregaFisica(field="entregafisica")
    estado = ColumnaDestinoEstado()

    class Meta:
        model = Destino
        id = "tabladbEntradaP"
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
        super(TablaPersonalEntrada, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:personal_bandeja_entrada_listar")
