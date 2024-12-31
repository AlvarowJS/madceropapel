"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse_lazy, reverse

from apps.inicio.models import PersonaJuridica
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaAcciones


class TablaPJ(Table):
    ruc = Columna(field="ruc", header="RUC", position="center")
    razonsocial = Columna(field="razonsocial", header="Razón Social")
    nombrecomercial = Columna(field="nombrecomercial", header="Nombre Comercial")
    acciones = ColumnaAcciones(url_edit="appini:pj_editar", url_delete="appini:pj_eliminar", ventana_tamanio="lg")

    class Meta:
        model = PersonaJuridica
        id = "tablaPJ"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": "",
                "attrs": {
                    "data-modal-size": "lg"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaPJ, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="appini:pj_listar", kwargs={"modo": "O"})
        self.opts.toolbar[0]["url"] = reverse("appini:pj_agregar", kwargs={"modo": "O"})
