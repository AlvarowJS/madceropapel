"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django import forms
from django.conf import settings
from django_select2.forms import ModelSelect2Widget

from apps.inicio.models import Persona
from apps.organizacion.models import PeriodoTrabajo, Area, DocumentoTipoArea, Dependencia
from apps.tramite.models import Expediente, Documento
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.formularios import AppBaseModelForm


class comboPersonaEncargo(ModelSelect2Widget):
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


class EncargaturaForm(AppBaseModelForm):
    area = forms.ModelChoiceField(
        label="Encargar en",
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
        widget=comboPersonaEncargo(
            search_fields=[
                "apellidocompleto__icontains",
                "numero__startswith",
                "ultimoperiodotrabajo__area__nombre__icontains",
                "ultimoperiodotrabajo__area__siglas__icontains"
            ],
            max_results=10
        )
    )
    documentoanio = forms.ChoiceField(
        label="Año",
        choices=[],
        required=False
    )
    documentooficina = forms.ModelChoiceField(
        label="Oficina",
        required=False,
        queryset=Area.objects.filter(paracomisiones=False, activo=True).order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10
        )
    )
    documentotipo = forms.ModelChoiceField(
        label="Tipo",
        required=False,
        queryset=DocumentoTipoArea.objects.order_by("documentotipo__nombre"),
        widget=comboDocumentoTipo(
            search_fields=[
                "documentotipo__nombre__icontains",
            ],
            max_results=10,
            dependent_fields={"documentooficina": "area"}
        )
    )
    documentosustento = forms.ModelChoiceField(
        label="Documento",
        required=False,
        queryset=Documento.objects.filter(
            ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"],
            origentipo="O"
        ).order_by("-numero"),
        widget=comboDocumentoSustento(
            search_fields=["numero"],
            max_results=10,
            dependent_fields={
                "documentoanio": "anio",
                "documentotipo": "documentotipoarea"
            }
        )
    )

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "inicio", "fin", "persona", "documentoanio", "documentooficina",
            "documentotipo", "documentosustento"
        ]

    def __init__(self, *args, **kwargs):
        super(EncargaturaForm, self).__init__(*args, **kwargs)
        self.fields["fin"].required = True
        self.fields["inicio"].widget.attrs["data-sidebyside"] = "true"
        self.fields["fin"].widget.attrs["data-sidebyside"] = "true"
        self.fields["documentoanio"].choices = [
            (anio, anio) for anio  in
            range(datetime.datetime.now().year, settings.CONFIG_APP["AnioInicio"] - 1, -1)
        ]


class EncargaturaPuestoForm(AppBaseModelForm):
    cbdep = forms.ChoiceField(
        label="Dependencia",
        choices=[],
    )
    cbarea = forms.ModelChoiceField(
        label="Unidad de Organización",
        queryset=Area.objects.filter(activo=True, paracomisiones=False).order_by("nombre"),
        widget=MADModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10,
            data_view="apporg:trabajador_area_listar",
            dependent_fields={"cbdep": "padre"}
        )
    )
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.exclude(ultimoperiodotrabajo__isnull=True).order_by("apellidocompleto"),
        widget=comboPersonaEncargo(
            search_fields=[
                "apellidocompleto__icontains",
                "numero__startswith",
                "ultimoperiodotrabajo__area__nombre__icontains",
                "ultimoperiodotrabajo__area__siglas__icontains"
            ],
            max_results=10
        )
    )
    documentoanio = forms.ChoiceField(
        label="Año",
        choices=[],
        required=False
    )
    documentooficina = forms.ModelChoiceField(
        label="Oficina",
        required=False,
        queryset=Area.objects.filter(paracomisiones=False, activo=True).order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10
        )
    )
    documentotipo = forms.ModelChoiceField(
        label="Tipo",
        required=False,
        queryset=DocumentoTipoArea.objects.order_by("documentotipo__nombre"),
        widget=comboDocumentoTipo(
            search_fields=[
                "documentotipo__nombre__icontains",
            ],
            max_results=10,
            dependent_fields={"documentooficina": "area"}
        )
    )
    documentosustento = forms.ModelChoiceField(
        label="Documento",
        required=False,
        queryset=Documento.objects.filter(
            ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"],
            origentipo="O"
        ).order_by("-numero"),
        widget=comboDocumentoSustento(
            search_fields=["numero"],
            max_results=10,
            dependent_fields={
                "documentoanio": "anio",
                "documentotipo": "documentotipoarea"
            }
        )
    )

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "cbdep", "cbarea", "persona", "documentoanio", "documentooficina",
            "documentotipo", "documentosustento"
        ]

    def __init__(self, *args, **kwargs):
        super(EncargaturaPuestoForm, self).__init__(*args, **kwargs)
        dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
        dependencias = [(dependencia.codigo, dependencia.nombre.upper())]
        for rindente in Area.objects.filter(activo=True, paracomisiones=False, esrindente=True).order_by("nombre"):
            dependencias.append(
                (rindente.pk, rindente.nombre)
            )
        self.fields["cbdep"].choices = dependencias
        self.fields["documentoanio"].choices = [
            (anio, anio) for anio in
            range(datetime.datetime.now().year, settings.CONFIG_APP["AnioInicio"] - 1, -1)
        ]

    def clean(self):
        cl = super(EncargaturaPuestoForm, self).clean()
        self.instance.area = cl["cbarea"]
        return cl


class EncargaturaPuestoTerminarForm(AppBaseModelForm):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PeriodoTrabajo
        fields = ["oculto"]
