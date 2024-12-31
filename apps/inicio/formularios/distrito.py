"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import Distrito
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormDistrito(AppBaseModelForm):
    class Meta:
        model = Distrito
        fields = [
            "id", "codigo", "nombre", "poligonal", "latitud", "longitud",
            "provincia"
        ]
