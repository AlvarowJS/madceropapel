"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import DocumentoFirma
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaAsunto, ColumnaBandejaSeguimiento, \
    ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class TablaOficinaFirmaVB(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbFirmaVB")
    fecha = ColumnaFecha(field="creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonro")
    asunto = ColumnaAsunto(field="documento.asunto")
    destino = Columna(field="documento.ListaDestinos", header="Destino", sortable=False, searchable=False)
    elaborado = Columna(field="creador.persona.alias", header="Elaborado por")
    estado = Columna(field="documento.ultimoestado.estado", header="Estado")

    class Meta:
        model = DocumentoFirma
        id = "tabladbFirmaVBO"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "creado"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaOficinaFirmaVB, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:oficina_bandeja_firma_vb_listar", kwargs={"modo": "sf"})
