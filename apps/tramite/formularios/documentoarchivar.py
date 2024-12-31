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


class DocumentoArchivarForm(AppBaseModelForm):
    fecha = forms.DateField(required=True, initial=timezone.now().date())
    observacion = forms.CharField(widget=forms.Textarea, label="Observación", required=False)

    firstfield = "observacion"

    class Meta:
        model = Destino
        fields = ["fecha", "observacion"]


class DocumentoDesarchivarForm(AppBaseModelForm):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Destino
        fields = ["oculto"]
