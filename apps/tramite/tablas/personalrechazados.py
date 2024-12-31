"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime
from html import escape

from django.urls import reverse

from apps.tramite.models import Destino
from apps.tramite.tablas._campos import ColumnaBandejaSeguimiento, ColumnaExpediente, ColumnaDocumento, \
    ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import ColumnaFecha, Columna


class ColumnaAccionRechazo(Columna):
    def __init__(self):
        super(ColumnaAccionRechazo, self).__init__(
            field="expedientenro", header="", sortable=False, searchable=False,
            attrs={"class": "w-80px"}, position="center"
        )

    def render(self, obj):
        _result = ""
        _boton = "<a class='btn btn-xs btn-icon ml-1 btn-light-%s' href='%s' data-toggle='modal' " \
                 "data-target='#modal-principal-centro' title='%s' rel='tooltip'>" \
                 "<i class='%s'></i></a>"
        kwargs = {"pk": obj.pk}
        # Volver a Enviar
        _urlreenviar = reverse("apptra:personal_bandeja_rechazado_reenviar", kwargs=kwargs)
        _result += _boton % (
            "primary",
            _urlreenviar,
            'Enviar Nuevamente',
            'fas fa-sync'
        )
        # Anular Destino (solo si hay más destinos)
        if obj.documento.des_documento.exclude(pk=obj.pk).count() > 0:
            _urlranular = reverse("apptra:personal_bandeja_rechazado_anular", kwargs=kwargs)
            _result += _boton % (
                "danger",
                _urlranular,
                'Anular Emisión a Destino',
                'fas fa-times'
            )
        # Archivar
        _urlarchivar = reverse("apptra:personal_bandeja_rechazado_archivar", kwargs=kwargs)
        _result += _boton % (
            "info",
            _urlarchivar,
            'Archivar',
            'fas fa-file-archive'
        )
        return escape(_result)


class TablaPersonalRechazados(Table):
    confidencial = ColumnaBandejaConfidencial(field="expedientenro")
    seguimiento = ColumnaBandejaSeguimiento(field="expedientenro")
    expediente = ColumnaExpediente(field="expedientenro", tab="dbRechazados")
    fecha = ColumnaFecha(field="documento.estadoemitido.creado", header="Fecha", format="%d/%m/%Y %I:%M %p")
    documento = ColumnaDocumento(field="documentonrosiglas")
    destinoofi = Columna(field="periodotrabajo.area.nombrecorto", header="Oficina")
    destinoper = Columna(field="periodotrabajo.persona.alias", header="Personal")
    rechazadoel = ColumnaFecha(field="ultimoestado.creado", header="Rechazado el", format="%d/%m/%Y %I:%M %p")
    rechazadopor = Columna(field="ultimoestado.creador.persona.alias", header="Rechazado por")
    rechazadoobs = Columna(field="ultimoestado.observacion", header="Motivo")
    acciones = ColumnaAccionRechazo()

    class Meta:
        model = Destino
        id = "tabladbRechazadosP"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "documento.estadoemitido.creado"
        }
        filter_tipodoc = {
            "field": "documento.documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaPersonalRechazados, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:personal_bandeja_rechazado_listar")
