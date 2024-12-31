"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.models import TipoDocumentoIdentidad
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormTipoDocumentoIdentidad(AppBaseModelForm):
    class Meta:
        model = TipoDocumentoIdentidad
        fields = [
            "id", "nombre", "codigo", "longitud", "tipo", "codigosunat",
            "exacto", "abreviatura", "buscareniec", "parapersona", "buscasunat"
        ]
