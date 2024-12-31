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
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class TablaPersonalRecepcionados(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbRecepcionados")
    fecha = ColumnaFecha(field="documento.ultimoestado.creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonro")
    asunto = ColumnaAsunto(field="documento.asunto")
    remitente = Columna(field="remitente", header="Remitente")
    inffis = ColumnaInformacionFisica()
    estado = ColumnaDestinoEstado()

    class Meta:
        model = Destino
        id = "tabladbRecepcionadosP"
        selectrowcheckbox = True
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "documento.ultimoestado.creado"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }
        # toolbar = [
        #     {
        #         "id": "btnAtenderProfesional",
        #         "icono": "fas fa-user-tag fa-1x",
        #         "texto": "Atender",
        #         # "modal": "#modal-principal-centro",
        #         "url": "#",
        #         "attrs": {
        #             "data-modal-size": "md",
        #             "campo": "2"
        #         }
        #     },
        #     {
        #         "id": "btnArchivar",
        #         "icono": "far fa-file-archive fa-1x",
        #         "clase": "btn-info",
        #         "texto": "Archivar",
        #         # "modal": "#modal-principal-centro",
        #         "url": "#",
        #         "attrs": {
        #             "data-modal-size": "md",
        #             "campo": "3"
        #         }
        #     },
        #     {
        #         "id": "btnAnular",
        #         "icono": "fas fa-undo fa-1x",
        #         "clase": "btn-danger",
        #         "texto": "Anular",
        #         # "modal": "#modal-principal-centro",
        #         "url": "#",
        #         "attrs": {
        #             "data-modal-size": "md",
        #             "campo": "4"
        #         }
        #     }
        # ]

    def __init__(self, request, estados, *args, **kwargs):
        super(TablaPersonalRecepcionados, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(
            viewname="apptra:personal_bandeja_recepcionado_listar",
            kwargs={"estados": estados}
        )
