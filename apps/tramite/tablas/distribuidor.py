"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse

from apps.tramite.models import Distribuidor
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha, ColumnaAcciones


class ColumnaTipo(Columna):
    def render(self, obj):
        _result = super(ColumnaTipo, self).render(obj)
        color = "info" if obj.tipo == "M" else "success"
        icono = "fas fa-motorcycle text-" if obj.tipo == "M" else "fas fa-shipping-fast text-"
        icono += color
        _result = "<span class='label label-light-%s label-inline'><i class='%s mr-2'></i> %s</span>" % (
            color,
            icono,
            _result)
        return _result


class ColumnaEstado(Columna):
    def render(self, obj):
        _result = "<span class='text-%s'>%s</span>" % (
            'default' if obj.estado else 'secondary',
            'Activo' if obj.estado else 'Inactivo',
        )
        return _result


class TablaDistribuidores(Table):
    tipodoc = Columna(field="documentotipo", header="Tipo")
    numero = Columna(field="documentonumero", header="Número")
    nombre = Columna(field="nombre", header="Nombre")
    tipo = ColumnaTipo(field="tipo", header="Tipo", position="center")
    inicio = ColumnaFecha(field="inicio", header="Inicio")
    fin = ColumnaFecha(field="fin", header="Fin")
    estado = ColumnaEstado(field="estado", header="Estado", position="center")
    acciones = ColumnaAcciones(
        url_edit="apptra:distribuidor_editar",
        url_delete="apptra:distribuidor_eliminar",
        ventana_tamanio="lg",
    )

    class Meta:
        model = Distribuidor
        id = "tablaDistribuidor"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": "#",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, request, *args, **kwargs):
        super(TablaDistribuidores, self).__init__(request, *args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apptra:distribuidor_listar")
        self.opts.toolbar[0]["url"] = reverse(viewname="apptra:distribuidor_agregar")
