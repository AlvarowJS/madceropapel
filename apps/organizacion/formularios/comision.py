"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django import forms
from django.conf import settings
from django.db.models import Count, Q
from django_select2.forms import ModelSelect2Widget

from apps.inicio.models import Persona, Cargo
from apps.organizacion.formularios.encargatura import comboDocumentoTipo, comboDocumentoSustento
from apps.organizacion.models import Area, DocumentoTipoArea, PeriodoTrabajo
from apps.tramite.models import Documento
from modulos.utiles.clases.campos import RadioSelectWidget
from modulos.utiles.clases.formularios import AppBaseModelForm, AppBaseForm


class comboPersona(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s" % (
            obj.numero,
            obj.apellidocompleto
        )


class comboCargoFull(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.nombrem


class FormComision(AppBaseModelForm):
    modocrea = forms.ChoiceField(
        label="",
        required=False,
        choices=[("EX", "Si Existe"), ("NE", "No Existe")],
        widget=RadioSelectWidget(
            clase="justify-content-center"
        ),
        initial="EX",
    )
    comision = forms.ModelChoiceField(
        queryset=Area.objects.filter(paracomisiones=True, id__gt=1, ).order_by("nombre"),
        required=False,
        widget=ModelSelect2Widget(
            search_fields=["nombre__icontains"],
            max_results=10
        )
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.filter(
            paracomision=True,
            esprincipal=True
        ).order_by("nombrem"),
        widget=comboCargoFull(
            search_fields=["nombrem__icontains"],
            max_results=10
        )
    )
    presidente = forms.ModelChoiceField(
        label="Persona",
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            search_fields=[
                "numero__startswith",
                "apellidocompleto__icontains"
            ],
            max_results=10
        )
    )
    documentoanio = forms.ChoiceField(
        label="Año",
        choices=[],
        required=True
    )
    documentooficina = forms.ModelChoiceField(
        label="Unidad Organizacional",
        required=True,
        queryset=Area.objetos.filter(
            paracomisiones=False,
            activo=True
        ).annotate(
            docscomi=Count(
                "documentotipoarea__documentotipo",
                filter=Q(documentotipoarea__documentotipo__autorizacomision=True)
            )
        ).filter(
            docscomi__gt=0
        ).order_by("nombre"),
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
        required=True,
        queryset=DocumentoTipoArea.objects.filter(
            documentotipo__autorizacomision=True
        ).order_by("documentotipo__nombre"),
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
        required=True,
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

    firstfield = "nombre"

    class Meta:
        model = Area
        fields = [
            "nombre", "cargo", "nombrecorto", "siglas", "presidente",
            "documentoanio", "documentooficina", "documentotipo",
            "documentosustento"
        ]

    def __init__(self, *args, **kwargs):
        super(FormComision, self).__init__(*args, **kwargs)
        self.fields["documentoanio"].choices = [
            (anio, anio) for anio in
            range(datetime.datetime.now().year, settings.CONFIG_APP["AnioInicio"] - 1, -1)
        ]
        self.fields["nombre"].required = False
        self.fields["nombrecorto"].required = False
        self.fields["siglas"].required = False


class FormComisionDirecta(AppBaseModelForm):
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.filter(
            paracomision=True,
            esprincipal=True
        ).order_by("nombrem"),
        widget=comboCargoFull(
            search_fields=["nombrem__icontains"],
            max_results=10
        )
    )
    presidente = forms.ModelChoiceField(
        label="Persona",
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            search_fields=[
                "numero__startswith",
                "apellidocompleto__icontains"
            ],
            max_results=10
        )
    )
    firstfield = "nombre"

    class Meta:
        model = Area
        fields = [
            "cargo", "nombre", "nombrecorto", "siglas", "presidente"
        ]

    def __init__(self, *args, **kwargs):
        super(FormComisionDirecta, self).__init__(*args, **kwargs)


class FormApoyoComision(AppBaseForm, forms.Form):
    cbComisionApoyo = forms.ModelChoiceField(
        label="Comisión",
        queryset=Area.objects.filter(paracomisiones=True, activo=True).order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=["nombre__icontains"],
            max_results=10
        )
    )


class comboComisionApoyoPersona(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % (
            obj.apellidocompleto
        )


class ComisionApoyoForm(AppBaseModelForm):
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.exclude(ultimoperiodotrabajo__isnull=True).order_by("apellidocompleto"),
        widget=comboComisionApoyoPersona(
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
            "inicio", "fin", "persona"
        ]

    def __init__(self, *args, **kwargs):
        super(ComisionApoyoForm, self).__init__(*args, **kwargs)
        self.fields["inicio"].widget.attrs["data-sidebyside"] = "true"
        self.fields["fin"].widget.attrs["data-sidebyside"] = "true"
