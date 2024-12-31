"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import Departamento
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormDepartamento(AppBaseModelForm):
    class Meta:
        model = Departamento
        fields = [
            "id", "nombre", "pais", "codigo"
        ]
