"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from apps.inicio.formularios.persona import fotografia
from apps.tramite.models import DocumentoTipoPlantilla
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormDocumentoTipoPlantilla(AppBaseModelForm):
    archivof = forms.CharField()
    archivoc = forms.CharField(required=False)
    archivop = forms.CharField(required=False)

    class Meta:
        model = DocumentoTipoPlantilla
        fields = [
            "documentotipo", "dependencia", "referenciatabs"
        ]

    def clean(self):
        cl = super(FormDocumentoTipoPlantilla, self).clean()
        if cl.get("archivof"):
            self.instance.archivo = fotografia(cl["archivof"])
        if cl.get("archivoc"):
            self.instance.archivoparacontenido = fotografia(cl["archivoc"])
        if cl.get("archivop"):
            self.instance.archivoposfirma = fotografia(cl["archivop"])
        return cl
