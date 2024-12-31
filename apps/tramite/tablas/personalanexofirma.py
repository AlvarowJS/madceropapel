"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import AnexoFirma
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaBandejaSeguimiento, \
    ColumnaBandejaConfidencial
from apps.tramite.tablas.oficinaanexofirma import ColumnaAnexo, ColumnaFirmar
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class TablaPersonalAnexoFirmaVB(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbFirmaVB")
    fecha = ColumnaFecha(field="creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaAnexo(field="anexo.descripcion", header="Documento")
    asunto = Columna(field="anexo.documento.asunto", displaytext="anexo.documento.asuntocorto", header="Asunto")
    elaborado = Columna(field="creador.persona.apellidocompleto", header="Elaborado por")
    firmar = ColumnaFirmar()

    class Meta:
        model = AnexoFirma
        id = "tabladbAnexoFirmaVBP"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "creado"
        }
        filter_tipodoc = {
            "field": "anexo.documento.documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaPersonalAnexoFirmaVB, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:personal_anexo_firma_vb_listar", kwargs={"modo": "sf"})
