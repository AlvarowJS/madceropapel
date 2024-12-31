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


class TablaPersonalFirmaVB(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbFirmaVB")
    fecha = ColumnaFecha(field="creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonro")
    asunto = ColumnaAsunto(field="documento.asunto")
    destino = Columna(field="documento.ListaDestinos", header="Destino", searchable=False, sortable=False)

    class Meta:
        model = DocumentoFirma
        id = "tabladbFirmaVBP"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "creado"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaPersonalFirmaVB, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:personal_bandeja_firma_vb_listar", kwargs={"modo": "sf"})
