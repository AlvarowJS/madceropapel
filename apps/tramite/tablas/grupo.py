"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse

from apps.organizacion.models import PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna


class TablaDocumentoDestinoGrupo(Table):
    dirigidoa = Columna(field="persona.apellidocompleto", header="Nombre", sortable=False)
    cargo = Columna(field="cargonombre", header="Cargo", sortable=False)
    coddep = Columna(field="area.dependencia.codigo", visible=False)
    codarea = Columna(field="area.pk", visible=False)
    nomarea = Columna(field="areacondep", visible=False)

    class Meta:
        model = PeriodoTrabajo
        id = "tablaDocumentoDestinoGrupo"
        selectrowcheckbox = True
        page_length = 100
        search = False
        scrollable = True
        info = False

    def __init__(self, tipo):
        super(TablaDocumentoDestinoGrupo, self).__init__()
        self.opts.ajax_source = reverse(viewname="apptra:documento_destino_grupo_listar", kwargs={"tipo": tipo})
