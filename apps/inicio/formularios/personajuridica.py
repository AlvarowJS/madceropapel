"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from apps.inicio.models import PersonaJuridica, Pais, Distrito
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormPersonaJuridica(AppBaseModelForm):
    pais_id = forms.IntegerField(required=False)
    ubigeo_id = forms.IntegerField(required=False)

    class Meta:
        model = PersonaJuridica
        fields = [
            "ruc", "razonsocial", "nombrecomercial", "direccion", "pais_id", "ubigeo_id",
            "referencia", "correo", "telefono", "representante", "representantecargo",
            "interopera", "consultaruc"
        ]

    def clean(self):
        cl = super(FormPersonaJuridica, self).clean()
        if cl["pais_id"]:
            self.instance.pais = Pais.objects.get(pk=cl["pais_id"])
        if cl["ubigeo_id"]:
            self.instance.ubigeo = Distrito.objects.get(pk=cl["ubigeo_id"])
        return cl

    def __init__(self, *args, **kwargs):
        super(FormPersonaJuridica, self).__init__(*args, **kwargs)
        self.fields["consultaruc"].input_formats[0] = "%Y-%m-%d"
