"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import Cargo
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormCargo(AppBaseModelForm):
    class Meta:
        model = Cargo
        fields = [
            "id", "nombrem", "nombref", "nombrecorto", "paracomision", "esprincipal",
            "paraunidad"
        ]
