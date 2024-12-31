"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime
from html import escape

from django.urls import reverse

from apps.tramite.models import Documento
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaDocumento, ColumnaBandejaSeguimiento, ColumnaAsunto, \
    ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaEstado(Columna):
    def render(self, obj):
        _result = super(ColumnaEstado, self).render(obj)
        _color = "primary" if obj.ultimoestado.estado == "PY" else "danger"
        _result = "<span class='label label-inline label-outline-%s'>%s</span>" % (
            _color,
            _result
        )
        return escape(_result)


class TablaOficinaEnProyecto(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbEnProyecto")
    fecha = ColumnaFecha(field="fecha", header="Fecha")
    documento = ColumnaDocumento(field="documentonrosiglas")
    asunto = ColumnaAsunto(field="asunto")
    destino = Columna(field="ListaDestinos", header="Destino", searchable=False, sortable=False)
    elaborado = Columna(field="creador.persona.alias", header="Elaborado por")
    estado = ColumnaEstado(field="ultimoestado.estado", header="Estado", position="center", header_attrs={"style": "width: 75px"})

    class Meta:
        model = Documento
        id = "tabladbEnProyectoO"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "fecha"
        }
        filter_tipodoc = {
            "field": "documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaOficinaEnProyecto, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:oficina_bandeja_en_proyecto_listar")
