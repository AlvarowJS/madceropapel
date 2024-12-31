"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.urls import reverse

from apps.tramite.models import AnexoFirma
from apps.tramite.tablas._campos import ColumnaExpediente, ColumnaAsunto, ColumnaBandejaSeguimiento, \
    ColumnaBandejaConfidencial
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaAnexo(Columna):
    def render(self, obj):
        _result = super(ColumnaAnexo, self).render(obj)
        cadenaUrl = "viewPDF('%s://%s%s','%s','%s','%s')" % (
            obj.scheme,
            obj.host,
            reverse(viewname="apptra:documento_anexo_descargar", kwargs={"pk": obj.anexo.pk}),
            _result,
            obj.token,
            "anxnew" + str(obj.pk)
        )
        _result = '<a class="text-nowrap btn-hover-light-primary puntero" ' \
                  'onclick="%s">%s</a>' % (
                      cadenaUrl,
                      _result
                  )
        return _result


class ColumnaFirmar(Columna):
    def __init__(self):
        super(ColumnaFirmar, self).__init__(
            field="creador.persona", header="Firmar", position="center", searchable=False, sortable=False
        )

    def render(self, obj):
        _result = '<a class="btn-firmar-anx btn btn-xs btn-light-primary btn-icon ml-2" rel="tooltip" ' + \
                  'title="Firmar Anexo" data-codigo="%s">' + \
                  '<i class="fas fa-pen-nib"></i>' + \
                  '</a><div></div>'
        _result = _result % obj.pk
        return _result


class TablaOficinaAnexoFirmaVB(Table):
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
        id = "tabladbAnexoFirmaVBO"
        filter_date = {
            "inicio": datetime.datetime.now().date().strftime("01/01/%Y"),
            "fin": datetime.datetime.now().date().strftime("31/12/%Y"),
            "field": "creado"
        }
        filter_tipodoc = {
            "field": "anexo.documento.documentotipoarea.documentotipo"
        }

    def __init__(self, request, *args, **kwargs):
        super(TablaOficinaAnexoFirmaVB, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:oficina_anexo_firma_vb_listar", kwargs={"modo": "sf"})
