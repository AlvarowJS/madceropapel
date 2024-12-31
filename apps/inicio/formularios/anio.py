"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import Anio
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormAnio(AppBaseModelForm):
    class Meta:
        model = Anio
        fields = [
            "id", "numero", "denominacion", "nombredecenio"
        ]
