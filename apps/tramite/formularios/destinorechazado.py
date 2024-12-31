"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.utils import timezone

from apps.tramite.models import Destino, DestinoEstado
from modulos.utiles.clases.formularios import AppBaseModelForm


class RechazadoReenviarForm(AppBaseModelForm):
    observacion = forms.CharField(
        label="Observación",
        max_length=DestinoEstado._meta.get_field("observacion").max_length,
        required=True,
        widget=forms.Textarea()
    )
    firstfield = "observacion"

    class Meta:
        model = Destino
        fields = [
            "observacion"
        ]


class RechazadoAnularForm(AppBaseModelForm):
    observacion = forms.CharField(
        label="Observación",
        max_length=DestinoEstado._meta.get_field("observacion").max_length,
        required=True,
        widget=forms.Textarea()
    )
    firstfield = "observacion"

    class Meta:
        model = Destino
        fields = [
            "observacion"
        ]


class RechazadoArchivarForm(AppBaseModelForm):
    fecha = forms.DateField(required=True, initial=timezone.now().date())
    observacion = forms.CharField(
        label="Observación",
        max_length=DestinoEstado._meta.get_field("observacion").max_length,
        required=True,
        widget=forms.Textarea()
    )
    firstfield = "observacion"

    class Meta:
        model = Destino
        fields = [
            "fecha", "observacion"
        ]
