"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse

from apps.organizacion.models import DocumentoTipoArea
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaAcciones


class TablaDocumentoTipoArea(Table):
    documentotipo = Columna(field="documentotipo.nombre", header="Tipo de Documento")
    acciones = ColumnaAcciones(url_delete="apporg:documentotipoarea_eliminar")

    class Meta:
        model = DocumentoTipoArea
        id = "tablaDocumentoTipoArea"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": "#",
                "attrs": {
                    "data-modal-size": "md",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaDocumentoTipoArea, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:documentotipoarea_listar", kwargs={"area": 0})
        self.opts.toolbar[0]["url"] = reverse(viewname="apporg:documentotipoarea_agregar", kwargs={"area": 0})
