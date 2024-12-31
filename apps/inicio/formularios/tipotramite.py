"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.models import TipoTramite
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormTipoTramite(AppBaseModelForm):
    class Meta:
        model = TipoTramite
        fields = [
            "id", "codigo", "nombre", "estado", "duenio"
        ]
