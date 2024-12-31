"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import Pais
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormPais(AppBaseModelForm):
    class Meta:
        model = Pais
        fields = [
            "id", "nombre", "iso2", "nacionalidad"
        ]
