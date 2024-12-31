"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import Documento
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaBandejaSeguimiento, ColumnaAsunto, \
    ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class TablaOficinaEmitidos(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEmitidos")
    fechaemision = ColumnaFecha(field="estadoemitido.creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonrosiglas")
    asunto = ColumnaAsunto(field="asunto")
    destino = Columna(field="ListaDestinos", header="Destino", sortable=False, searchable=False)
    destinorechazos = Columna(field="rechazos", header="", sortable=False, visible=False)
    elaborado = Columna(field="creador.persona.alias", header="Elaborado por")
    estado = Columna(field="ultimoestado.estado", header="Estado")

    class Meta:
        model = Documento
        id = "tabladbEmitidosO"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "estadoemitido.creado"
        }
        filter_tipodoc = {
            "field": "documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaOficinaEmitidos, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:oficina_bandeja_emitidos_listar")
