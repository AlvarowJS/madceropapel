"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.models import TipoProveido
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormTipoProveido(AppBaseModelForm):
    class Meta:
        model = TipoProveido
        fields = [
            "id", "nombre", "estado"
        ]
