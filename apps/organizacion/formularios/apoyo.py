"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django_select2.forms import ModelSelect2Widget

from apps.inicio.models import Persona
from apps.organizacion.models import PeriodoTrabajo, Area
from modulos.utiles.clases.campos import RadioSelectWidget
from modulos.utiles.clases.formularios import AppBaseModelForm


class comboPersonaApoyo(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - %s" % (
            obj.numero,
            obj.apellidocompleto,
            obj.ultimoperiodotrabajo.area.nombre
        )


class comboDocumentoTipo(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.documentotipo.nombre


class comboDocumentoSustento(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.nombreDocumentoParteNumero()


class ApoyoForm(AppBaseModelForm):
    apoyoforma = forms.ChoiceField(
        label="",
        required=False,
        choices=PeriodoTrabajo.APOYOFORMAS,
        widget=RadioSelectWidget(
            clase="justify-content-center"
        ),
        initial="A",
    )
    area = forms.ModelChoiceField(
        label="Apoyar en",
        queryset=Area.objects.filter(paracomisiones=False, activo=True).order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10
        )
    )
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.exclude(ultimoperiodotrabajo__isnull=True).order_by("apellidocompleto"),
        widget=comboPersonaApoyo(
            search_fields=[
                "apellidocompleto__icontains",
                "numero__startswith",
                "ultimoperiodotrabajo__area__nombre__icontains",
                "ultimoperiodotrabajo__area__siglas__icontains"
            ],
            max_results=10
        )
    )

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "inicio", "fin", "persona", "apoyoforma"
        ]

    def __init__(self, *args, **kwargs):
        super(ApoyoForm, self).__init__(*args, **kwargs)
        self.fields["fin"].required = True
        self.fields["inicio"].widget.attrs["data-sidebyside"] = "true"
        self.fields["fin"].widget.attrs["data-sidebyside"] = "true"


class ApoyoAutorizarForm(AppBaseModelForm):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = PeriodoTrabajo
        fields = ["oculto"]
