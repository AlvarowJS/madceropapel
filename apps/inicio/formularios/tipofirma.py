"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import TipoFirma
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormTipoFirma(AppBaseModelForm):
    class Meta:
        model = TipoFirma
        fields = [
            "id", "nombre", "codigo"
        ]
