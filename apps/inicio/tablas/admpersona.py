"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse

from apps.inicio.models import Persona
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha, ColumnaBoolean, ColumnaAcciones
from modulos.utiles.clases.formularios import EstadosSiNo


class TablaAdmPersona(Table):
    tipodocumento = Columna(field="tipodocumentoidentidad.codigo", header="Tipo", position="center")
    numero = Columna(field="numero", header="Número", position="center")
    nombrecompleto = Columna(field="nombrecompleto", header="Nombre")
    sexo = Columna(field="sexo", header="Sexo")
    nacimiento = ColumnaFecha(field="nacimiento", header="Nacimiento")
    confirmado = Columna(field="confirmado", header="Confirmado", position="center")
    consultadni = ColumnaFecha(field="consultadni", header="Consulta DNI", format="%d/%m/%Y %I:%M %p")
    acciones = ColumnaAcciones(url_edit="appini:adm_persona_editar", ventana_tamanio="lg")

    class Meta:
        model = Persona
        id = "tablaAdmPersona"
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
        super(TablaAdmPersona, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="appini:adm_persona_listar")
        self.opts.toolbar[0]["url"] = reverse("appini:adm_persona_agregar")
