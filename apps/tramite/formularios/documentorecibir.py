"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from apps.tramite.models import Destino
from modulos.utiles.clases.formularios import AppBaseModelForm


class DestinoRecibirForm(AppBaseModelForm):
    codest = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destino
        fields = ["codest"]
