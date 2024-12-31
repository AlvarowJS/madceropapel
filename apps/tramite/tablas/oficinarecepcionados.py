"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import Destino
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaAsunto, ColumnaDestinoEstado, \
    ColumnaBandejaSeguimiento, ColumnaInformacionFisica, ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha, ColumnaAcciones


class TablaOficinaRecepcionados(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbRecepcionados")
    fecha = ColumnaFecha(field="ultimoestado.creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonrosiglas")
    asunto = ColumnaAsunto(field="documento.asunto")
    remitente = Columna(field="remitente", header="Remitente")
    inffis = ColumnaInformacionFisica()
    estado = ColumnaDestinoEstado()

    class Meta:
        model = Destino
        id = "tabladbRecepcionadosO"
        selectrowcheckbox = True
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "ultimoestado.creado"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }

    def __init__(self, request, estados, *args, **kwargs):
        super(TablaOficinaRecepcionados, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(
            viewname="apptra:oficina_bandeja_recepcionados_listar",
            kwargs={"estados": estados}
        )
