"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import Documento
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaAsunto, ColumnaBandejaSeguimiento, \
    ColumnaBandejaConfidencial
from apps.tramite.tablas.oficinaenproyecto import ColumnaEstado
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class TablaPersonalEnProyecto(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEnProyecto")
    fecha = ColumnaFecha(field="fecha", header="Fecha", )
    documento = ColumnaDocumento(field="documentonro")
    asunto = ColumnaAsunto(field="asunto")
    destino = Columna(field="ListaDestinos", header="Destino", searchable=False, sortable=False)
    estado = ColumnaEstado(field="ultimoestado.estado", header="Estado", position="center")

    class Meta:
        model = Documento
        id = "tabladbEnProyectoP"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "fecha"
        }
        filter_tipodoc = {
            "field": "documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaPersonalEnProyecto, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:personal_bandeja_en_proyecto_listar")
