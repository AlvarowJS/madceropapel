"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse, reverse_lazy

from apps.organizacion.models import Proyeccion
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaAcciones, ColumnaFecha


class TablaProyeccion(Table):
    area = Columna(field="areaorigen.nombre", header="Unidad Organizacional donde puede proyectar")
    registro = ColumnaFecha(field="creado", header="Registrado el", format="%d/%m/%Y %I:%M %p")
    acciones = ColumnaAcciones(url_delete="apporg:proyeccion_eliminar")

    class Meta:
        model = Proyeccion
        id = "tablaProyeccion"
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

    def __init__(self, trabajador=None, *args, **kwargs):
        super(TablaProyeccion, self).__init__(*args, **kwargs)
        idtrabajador = 0 if not trabajador else trabajador.pk
        self.opts.ajax_source = reverse(viewname="apporg:proyeccion_listar", kwargs={"pt": idtrabajador})
        self.opts.toolbar[0]["url"] = reverse(viewname="apporg:proyeccion_agregar", kwargs={"pt": idtrabajador})


class TablaProyeccionArea(Table):
    trabajador = Columna(field="periodotrabajo.persona.apellidocompleto", header="Trabajador que puede proyectar")
    area = Columna(field="periodotrabajo.area.nombre", header="Unidad Organizacional desde donde proyecta")
    creado = ColumnaFecha(field="creado", header="Registrado el", format="%d/%m/%Y %I:%M %p")
    creador = Columna(field="creador.persona.alias", header="Registrado por")
    acciones = ColumnaAcciones(url_delete="apporg:proyeccionarea_eliminar")

    class Meta:
        model = Proyeccion
        id = "tablaProyeccionArea"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apporg:proyeccionarea_agregar"),
                "attrs": {
                    "data-modal-size": "md",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, trabajador=None, *args, **kwargs):
        super(TablaProyeccionArea, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:proyeccionarea_listar")
