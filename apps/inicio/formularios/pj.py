"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django_select2.forms import ModelSelect2Widget

from apps.inicio.models import PersonaJuridica, Pais, Distrito, Persona
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.formularios import AppBaseForm, AppBaseModelForm


class formPJSelector(AppBaseForm, forms.Form):
    tipopj = forms.ChoiceField(
        label="Tipo",
        choices=PersonaJuridica.TIPOS[1:],
        required=False,
        initial="O"
    )


class comboUbigeo(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return obj.RutaDepartamento()


class comboPersona(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.apellidocompleto


class PJForm(AppBaseModelForm):
    pais = forms.ModelChoiceField(
        queryset=Pais.objects.order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=["nombre__icontains"],
            max_results=10
        )
    )
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
        )
    )
    representante = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            search_fields=["apellidocompleto__icontains"],
            max_results=10
        ),
        required=False
    )

    class Meta:
        model = PersonaJuridica
        fields = [
            "ruc", "razonsocial", "nombrecomercial", "direccion", "referencia",
            "correo", "telefono", "representante", "representantecargo",
            "pais", "ubigeo"
        ]
