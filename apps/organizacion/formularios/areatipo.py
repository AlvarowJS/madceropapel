"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.organizacion.models import AreaTipo
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormAreaTipo(AppBaseModelForm):
    class Meta:
        model = AreaTipo
        fields = [
            "id", "nombre", "codigo", "icono", "paracomision"
        ]
