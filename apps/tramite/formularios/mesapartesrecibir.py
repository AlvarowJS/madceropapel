"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from modulos.utiles.clases.campos import CheckWidget
from modulos.utiles.clases.formularios import AppBaseForm


class DestinoMensajeriaRecibir(forms.Form):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput())


class DestinoMensajeriaDevolver(AppBaseForm, forms.Form):
    observacion = forms.CharField(label="Observación", required=True, widget=forms.Textarea())
    allexpediente = forms.BooleanField(
        label="Devolver todo el documento",
        initial=False,
        required=False,
        widget=CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
    )

    firstfield = "observacion"
