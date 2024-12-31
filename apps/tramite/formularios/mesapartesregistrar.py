"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django import forms
from django.urls import reverse
from django.utils import timezone
from django_select2.forms import ModelSelect2Widget

from apps.inicio.models import Persona, PersonaJuridica, Distrito, TipoDocumentoIdentidad
from apps.organizacion.models import DocumentoTipoArea
from apps.tramite.models import Documento
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.campos import AppInputNumber, TextAreaAutoWidget, AppInputTextWidget, RadioSelectWidget, \
    ModelFileField, CheckWidget
from modulos.utiles.clases.formularios import AppBaseModelForm


class comboPersona(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.apellidocompleto


class comboDocumentoTipo(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.documentotipo.nombre


class comboDistritoFull(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - %s" % (
            obj.provincia.departamento.nombre,
            obj.provincia.nombre,
            obj.nombre
        )


class MesaPartesRegistrarForm(AppBaseModelForm):
    personajuridicatipo = forms.ChoiceField(
        required=False,
        choices=Documento.PERSONAJURIDICATIPO,
        initial=Documento.PERSONAJURIDICATIPO[0][0]
    )
    personajuridicaruc = forms.CharField(
        label="RUC",
        min_length=11,
        max_length=11,
        widget=AppInputTextWidget(
            mask="9" * 11
        ),
        required=False
    )
    personajuridica = forms.ModelChoiceField(
        queryset=PersonaJuridica.objects.filter(tipo="R").order_by("razoncomercial"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "ruc__startswith",
                "razoncomercial__icontains"
            ],
            data_view="appini:personajuridica_listar"
        ),
        required=False
    )
    personajuridicarz = forms.CharField(
        label="Razón Social",
        max_length=250,
        required=False,
    )
    ciudadanoemisortipo = forms.ModelChoiceField(
        label="Tipo de Documento",
        queryset=TipoDocumentoIdentidad.objects.filter(parapersona=True).order_by("pk"),
        widget=ModelSelect2Widget(
            search_fields=[
                "codigo__icontains",
                "nombre__icontains"
            ],
            max_results=10,
            data_view="appini:tipodocumentoidentidad_listar"
        )
    )
    ciudadanoemisorcodigo = forms.IntegerField(
        initial=-1,
        required=False,
        widget=forms.HiddenInput()
    )
    ciudadanoemisornumero = forms.CharField(
        label="Número",
        min_length=1,
        max_length=15,
        required=False
    )
    ciudadanoemisordni = forms.CharField(
        label="DNI",
        min_length=8,
        max_length=15,
        widget=AppInputTextWidget(
            mask="9" * 8
        ),
        required=False
    )
    ciudadanoemisor = forms.ModelChoiceField(
        queryset=Persona.objects.filter(tipodocumentoidentidad__codigo="DNI").order_by("apellidocompleto"),
        widget=comboPersona(
            max_results=10,
            search_fields=[
                "numero__startswith",
                "apellidocompleto__icontains"
            ],
            data_view="appini:persona_listar"
        ),
        required=False
    )
    ciudadanoemisorpaterno = forms.CharField(
        label="Ap. Paterno",
        max_length=50,
        required=False
    )
    ciudadanoemisormaterno = forms.CharField(
        label="Ap. Materno",
        max_length=50,
        required=False
    )
    ciudadanoemisornombres = forms.CharField(
        label="Nombres",
        max_length=50,
        required=False
    )
    ciudadanoemisorsexo = forms.BooleanField(
        label="Sexo",
        widget=CheckWidget(
            ontext="M",
            offtext="F",
            oncolor="primary",
            offcolor="danger"
        ),
        initial=True,
        required=False
    )
    ciudadanotramitadordni = forms.CharField(
        label="DNI",
        min_length=8,
        max_length=8,
        widget=AppInputTextWidget(
            mask="9" * 8
        ),
        required=False
    )
    ciudadanotramitador = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            max_results=10,
            search_fields=[
                "numero__startswith",
                "apellidocompleto__icontains"
            ],
            data_view="appini:persona_listar"
        ),
        required=False
    )
    numero = AppInputNumber(
        minimo=0,
        initial=0,
        css="text-center mr-4",
        required=True
    )
    folios = AppInputNumber(
        minimo=1,
        initial=1,
        css="text-center mr-4",
        required=True
    )
    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.order_by("provincia__departamento__nombre", "provincia__nombre", "nombre"),
        widget=comboDistritoFull(
            max_results=10,
            search_fields=[
                "nombre__icontains",
            ]
        ),
        required=True
    )
    documentotipoarea = comboDocumentoTipo(
        queryset=DocumentoTipoArea.objects.order_by("documentotipo__nombre"),
        required=True
    )
    contenido = ModelFileField(
        label="Archivo",
        required=False,
        extensiones=["pdf"],
        maxsize=1024 * 10
    )
    destinos = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    confidencial = forms.BooleanField(
        # label="Reservado/Confidencial",
        required=False,
        widget=CheckWidget(
            oncolor="danger",
            offcolor="primary",
            ontext="SI",
            offtext="NO"
        )
    )

    class Meta:
        model = Documento
        fields = [
            "remitentetipo", "personajuridicatipo", "personajuridicaruc", "personajuridica",
            "personajuridicarz", "ciudadanoemisortipo", "ciudadanoemisornumero",
            "ciudadanoemisordni", "ciudadanoemisor", "ciudadanoemisorpaterno",
            "ciudadanoemisormaterno", "ciudadanoemisornombres", "ciudadanoemisorsexo",
            "ciudadanocargo", "ciudadanoemisorcodigo", "confidencial",
            "telefono", "distrito", "direccion", "correo", "observacion", "documentotipoarea",
            "numero", "siglas", "fecha", "folios", "asunto", "ciudadanotramitadordni", "ciudadanotramitador",
            "areavirtualdestino", "contenido", "destinos",
            # "notificar",
        ]
        widgets = {
            "remitentetipo": RadioSelectWidget(
                clase="justify-content-center mb-4"
            )
        }

    def __init__(self, *args, **kwargs):
        super(MesaPartesRegistrarForm, self).__init__(*args, **kwargs)
        self.fields["asunto"].widget = TextAreaAutoWidget()
        self.fields["observacion"].widget = TextAreaAutoWidget()
        self.fields["documentotipoarea"].empty_label = "-" * 10
        self.fields["fecha"].initial = timezone.now().date()
        self.fields["fecha"].widget.attrs["data-enddate"] = datetime.datetime.now().strftime("%Y-%m-%d")
        self.fields["personajuridicarz"].widget.attrs["typeahead"] = reverse("apptra:mp_autocomplete_razonsocial")
        self.fields["ciudadanocargo"].widget.attrs["typeahead"] = reverse("apptra:mp_autocomplete_cargo")


class MesaPartesRegistrarDestinosForm(AppBaseModelForm):
    destinosmp = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Documento
        fields = [
            "destinosmp"
        ]


class MesaPartesRegistrarArchivosForm(AppBaseModelForm):
    archivosmp = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    archivosorden = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Documento
        fields = [
            "archivosmp", "archivosorden"
        ]


class MesaPartesEmitirForm(AppBaseModelForm):
    oculto = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Documento
        fields = [
            "oculto"
        ]
