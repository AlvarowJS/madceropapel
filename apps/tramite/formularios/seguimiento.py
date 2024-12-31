"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django import forms
from django.conf import settings

from modulos.utiles.clases.campos import AppInputNumber
from modulos.utiles.clases.formularios import AppBaseForm


class SeguimientoDirectoForm(AppBaseForm, forms.Form):
    # seg_dep = forms.ModelChoiceField(
    #
    # )
    seg_anio = forms.ChoiceField(
        label="Año",
        choices=[]
    )
    seg_num = AppInputNumber(
        minimo=1,
        css="form-control text-center",
        placeholder="N° Expediente"
    )

    def __init__(self, *args, **kwargs):
        super(SeguimientoDirectoForm, self).__init__(*args, **kwargs)
        self.fields["seg_anio"].choices = [
            (anio, anio) for anio in
            range(datetime.datetime.now().year, settings.CONFIG_APP["AnioInicio"] - 1, -1)
        ]
