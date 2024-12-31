"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.models import DocumentoTipo
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormDocumentoTipo(AppBaseModelForm):
    class Meta:
        model = DocumentoTipo
        fields = [
            "id", "codigo", "nombre", "nombrecorto", "esmultiple",
            "firmaavanzada", "firmamultiple", "mesadepartesvirtual",
            "paranotificacion", "plantillaautomatica", "usoexterno",
            "usoprofesional", "pordefecto", "autorizacomision",
            "esmultipledestino", "tieneforma", "siglassinproyeccion",
            "correlativounico", "paraderivacion"
        ]
