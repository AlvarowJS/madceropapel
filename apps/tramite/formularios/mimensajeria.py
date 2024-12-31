"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from apps.tramite.models import Documento
from modulos.utiles.clases.campos import CheckWidget
from modulos.utiles.clases.formularios import AppBaseForm, AppBaseModelForm


class FormMesaPartesMiMensajeria(AppBaseForm, forms.Form):
    cbmodo = forms.ChoiceField(
        choices=[("D", "Devueltos"), ("N", "No Devueltos"), ("T", "Todos")],
        initial="D"
    )


class MiMensajeriaAccionesForm(AppBaseModelForm):
    amodo = forms.ChoiceField(
        choices=[('PE', 'Reenviar'), ('AR', 'Archivar')]
    )
    aobservacion = forms.CharField(widget=forms.Textarea, label="Observación", required=False)
    atodos = forms.BooleanField(
        label="Todo el expediente",
        initial=False,
        required=False,
        widget=CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
    )
    firstfield = "aobservacion"

    class Meta:
        model = Documento
        fields = ["amodo", "aobservacion", "atodos"]
