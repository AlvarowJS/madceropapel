"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms

from apps.inicio.models import Persona, PersonaJuridica
from apps.tramite.models import Distribuidor
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.campos import AppInputTextWidget, RadioSelectWidget, CheckWidget
from modulos.utiles.clases.formularios import AppBaseModelForm, AppBaseForm


class comboPersona(MADModelSelect2Widget):
    search_fields = [
        "apellidocompleto__icontains",
        "numero__startswith"
    ]
    max_results = 10

    def label_from_instance(self, obj):
        return "%s" % obj.apellidocompleto


class comboPersonaJuridica(MADModelSelect2Widget):
    search_fields = [
        "razoncomercial__icontains",
        "ruc__startswith"
    ]
    max_results = 10

    def label_from_instance(self, obj):
        return "%s" % (obj.nombrecomercial or obj.razonsocial)


class FormDistribuidor(AppBaseModelForm):
    personadni = forms.CharField(
        label="DNI",
        max_length=8,
        min_length=8,
        widget=AppInputTextWidget(
            mask="9" * 8
        ),
        required=False
    )
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            data_view="appini:persona_listar"
        ),
        required=False
    )
    personajuridicaruc = forms.CharField(
        label="RUC",
        max_length=11,
        min_length=11,
        widget=AppInputTextWidget(
            mask="9" * 11
        ),
        required=False
    )
    personajuridica = forms.ModelChoiceField(
        queryset=PersonaJuridica.objects.order_by("razoncomercial"),
        widget=comboPersonaJuridica(
            data_view="appini:personajuridica_listar"
        ),
        required=False
    )
    firstfield = "personajuridicaruc"

    class Meta:
        model = Distribuidor
        fields = [
            "tipo", "persona", "personajuridica", "inicio", "fin", "estado"
        ]
        widgets = {
            "tipo": RadioSelectWidget()
        }

    def __init__(self, *args, **kwargs):
        super(FormDistribuidor, self).__init__(*args, **kwargs)
        self.fields["estado"].widget = CheckWidget(
            ontext="Activo",
            offtext="Inactivo",
            oncolor="primary",
            offcolor="warning"
        )
