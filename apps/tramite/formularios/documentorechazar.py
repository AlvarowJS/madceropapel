"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.utils import timezone

from apps.tramite.models import Destino
from modulos.utiles.clases.formularios import AppBaseModelForm


class DocumentoRechazarForm(AppBaseModelForm):
    observacion = forms.CharField(widget=forms.Textarea, label="Observación", required=True)

    firstfield = "observacion"

    class Meta:
        model = Destino
        fields = ["observacion"]
