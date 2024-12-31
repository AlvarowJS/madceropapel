"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.conf import settings

from apps.organizacion.models import Dependencia
from modulos.utiles.clases.campos import CheckWidget
from modulos.utiles.clases.formularios import AppBaseModelForm


class FormDependencia(AppBaseModelForm):
    firstfield = "nombre"

    class Meta:
        model = Dependencia
        fields = [
            "principal", "orden", "codigo", "nombre",
            "nombrecorto", "siglas", "direccion",
            "ubigeo", "telefono", "correo", "web",
            "ruc", "rucfirma", "padre",
            "titulodoc1", "titulodoc2", "usaniveles"
        ]

    def __init__(self, *args, **kwargs):
        super(FormDependencia, self).__init__(*args, **kwargs)
        if self.instance.codigo == settings.CONFIG_APP["Dependencia"]:
            del self.fields["direccion"]
            del self.fields["telefono"]
            del self.fields["correo"]
            del self.fields["web"]


class FormMiDependencia(AppBaseModelForm):
    firstfield = "direccion"

    class Meta:
        model = Dependencia
        fields = [
            "direccion", "telefono", "correo", "web",
            "sello_firmagrc", "sello_firma", "sello_vistobueno", "sello_cargo",
            "sello_firma_adicional"
        ]

    def __init__(self, *args, **kwargs):
        super(FormMiDependencia, self).__init__(*args, **kwargs)
        self.fields["sello_firmagrc"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
