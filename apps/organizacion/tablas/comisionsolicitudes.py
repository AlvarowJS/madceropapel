"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse

from apps.organizacion.models import PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaDocumentoSustento(Columna):
    def __init__(self, header, *args, **kwargs):
        super(ColumnaDocumentoSustento, self).__init__(
            field="area.nombre", searchable=False, sortable=False, header=header, position="center"
        )

    def render(self, obj):
        _result = ""
        primerpres = obj.area.trabajadores.filter(cargo__esprincipal=True).order_by("pk").first()
        if primerpres:
            if primerpres.documentosustento:
                # Creación de Comisión
                _result += "<a class='btn btn-primary btn-icon btn-xs' onclick='viewPDF(\"%s\", \"%s\", \"%s\")' " + \
                           "title='Ver documento de Comisión' rel='tooltip'>" + \
                           "<i class='fas fa-file-pdf'></i></a>"
                _result = _result % (
                    reverse("apptra:documento_descargar", kwargs={"pk": primerpres.documentosustento.pk}),
                    primerpres.documentosustento.nombreDocumentoNumero(),
                    obj.creador.auth_token.key
                )
            # Solicitud de Cambio de Presidente
        _result += "<a class='btn btn-primary btn-icon btn-xs ml-2' onclick='viewPDF(\"%s\", \"%s\", \"%s\")' " + \
                   "title='Ver documento de Nuevo Presidente' rel='tooltip'>" + \
                   "<i class='far fa-file-pdf'></i></a>"
        _result = _result % (
            reverse("apptra:documento_descargar", kwargs={"pk": obj.documentosustento.pk}),
            obj.documentosustento.nombreDocumentoNumero(),
            obj.creador.auth_token.key
        )
        return _result


class ColumnaAprobador(Columna):
    def render(self, obj):
        _result = super(ColumnaAprobador, self).render(obj)
        if not _result:
            _result = "<a href='%s' data-toggle='modal' data-target='#modal-principal-centro' rel='tooltip' " + \
                      "class='bs-tooltip btn btn-sm btn-clean btn-icon' data-modal-size='lg' " + \
                      "title='Aprobar'><i class='fas fa-check'></i></a>"
            _result = _result % reverse(viewname="apporg:comisionsolicitudes_aprobar", kwargs={"pk": obj.pk})
        return _result


class TablaComisionSolicitudes(Table):
    comision = Columna(field="area.nombre", header="Comisión")
    presidenteactual = Columna(field="area.jefeactual.persona.apellidocompleto", header="Presidente Actual")
    presidentenuevo = Columna(field="persona.apellidocompleto", header="Presidente Nuevo")
    solicitante = Columna(field="creador.persona.alias", header="Solicitante", position="center")
    solicitadoel = ColumnaFecha(field="creado", header="Solicitado el", format="%d/%m/%Y %I:%M %p")
    documentosustento = ColumnaDocumentoSustento(header="Documentos")
    aprobador = ColumnaAprobador(field="aprobador.persona.alias", header="Aprobador", position="center")

    class Meta:
        model = PeriodoTrabajo
        id = "tablaComisionSolicitudes"

    def __init__(self, *args, **kwargs):
        super(TablaComisionSolicitudes, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:comisionsolicitudes_listar")
