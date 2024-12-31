"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from modulos.utiles.clases.formularios import AppBaseForm


class FormBloqueo(AppBaseForm, forms.Form):
    clavebloqueo = forms.CharField(
        label="Ingrese su contraseña para desbloquear",
        widget=forms.PasswordInput(
            attrs={"class": "text-center"}
        ),
        required=True
    )
