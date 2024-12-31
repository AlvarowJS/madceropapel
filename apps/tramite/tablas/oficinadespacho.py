"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse, reverse_lazy

from apps.tramite.models import Documento
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaBandejaSeguimiento, ColumnaAsunto, \
    ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class TablaOficinaDespacho(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbDespacho")
    fecha = ColumnaFecha(field="ultimoestado.creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonrosiglas")
    asunto = ColumnaAsunto(field="asunto")
    destino = Columna(field="ListaDestinos", header="Destino", searchable=False, sortable=False)
    elaborado = Columna(field="creador.persona.nombrecompleto", header="Elaborado por")
    estado = Columna(field="estadoFirmas", header="Estado", searchable=False, sortable=False, position="center")
    esmultiple = Columna(
        field="documentotipoarea.documentotipo.esmultiple", searchable=False, sortable=False, visible=False
    )

    class Meta:
        model = Documento
        id = "tabladbDespachoO"
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
            {
                "id": "btnFirmaMasiva",
                "icono": "la la-pen-nib",
                "clase": "btn btn-rounded btn-sm btn-primary",
                "texto": "Firma Masiva",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apptra:oficina_bandeja_despacho_firmamasiva"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            },
            {
                "id": "btnEmisionMasiva",
                "icono": "fab la-telegram-plane",
                "clase": "btn btn-rounded btn-sm btn-primary",
                "texto": "Emisión Masiva",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apptra:oficina_bandeja_despacho_emisionmasiva"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            },
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaOficinaDespacho, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:oficina_bandeja_despacho_listar")
