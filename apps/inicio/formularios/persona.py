"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64

from django import forms

from apps.inicio.formularios.pj import comboUbigeo
from apps.inicio.models import Persona, Pais, Distrito
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormPersona(AppBaseModelForm):
    pais_id = forms.IntegerField(required=False)
    ubigeo_id = forms.IntegerField(required=False)
    foto = forms.CharField(required=False)

    class Meta:
        model = Persona
        fields = [
            "tipodocumentoidentidad", "numero", "nombres", "paterno", "materno",
            "sexo", "nacimiento", "pais", "ubigeo", "direccion", "referencia",
            "telefono", "correo", "confirmado", "consultadni", "foto"
        ]

    def clean(self):
        cl = super(FormPersona, self).clean()
        if cl.get("pais_id"):
            self.instance.pais = Pais.objects.get(pk=cl["pais_id"])
        if cl.get("ubigeo_id"):
            self.instance.ubigeo = Distrito.objects.get(pk=cl["ubigeo_id"])
        if cl.get("foto"):
            self.instance.fotografia = fotografia(cl["foto"])
        return cl

    def __init__(self, *args, **kwargs):
        super(FormPersona, self).__init__(*args, **kwargs)
        self.fields["nacimiento"].input_formats[0] = "%Y-%m-%d"
        self.fields["consultadni"].input_formats[0] = "%Y-%m-%d %H:%M:%S"


def fotografia(foto):
    _result = None
    if foto:
        _result = base64.b64decode(foto)
    return _result


class FormAdmPersona(AppBaseModelForm):
    ubigeo = forms.ModelChoiceField(
        label="UBIGEO",
        queryset=Distrito.objects.order_by(
            "provincia__departamento__nombre",
            "provincia__nombre",
            "nombre"
        ),
        widget=comboUbigeo(
            search_fields=[
                "nombre__icontains"
            ],
            max_results=10,
        ),
        required=False
    )

    class Meta:
        model = Persona
        fields = [
            "tipodocumentoidentidad", "numero", "nombres", "paterno", "materno",
            "sexo", "nacimiento", "ubigeo", "direccion", "referencia",
            "telefono", "correo"
        ]
