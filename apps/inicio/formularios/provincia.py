"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import Provincia
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormProvincia(AppBaseModelForm):
    class Meta:
        model = Provincia
        fields = [
            "id", "codigo", "nombre", "departamento", "capital", "latitud",
            "longitud", "poligonal", "puntocentral"
        ]
