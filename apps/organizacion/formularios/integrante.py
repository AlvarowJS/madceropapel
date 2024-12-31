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
from django.utils import timezone
from django.utils.timezone import make_aware
from django_select2.forms import ModelSelect2Widget
from pytz import UTC

from apps.inicio.models import Persona, Cargo
from apps.organizacion.formularios.comision import comboPersona
from apps.organizacion.formularios.encargatura import comboDocumentoTipo, comboDocumentoSustento
from apps.organizacion.formularios.trabajador import comboCargo
from apps.organizacion.models import PeriodoTrabajo, Area, DocumentoTipoArea
from apps.tramite.models import Documento
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.campos import AppInputTextWidget, WidgetFecha
from modulos.utiles.clases.formularios import AppBaseModelForm, AppBaseForm


class FormIntegrante(AppBaseModelForm):
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            data_view="appini:persona_listar",
            search_fields=[
                "apellidocompleto__icontains",
                "numero__startswith"
            ]
        )
    )
    cargo = forms.ModelChoiceField(
        label="Rol",
        queryset=Cargo.objects.filter(paracomision=True).order_by("nombrecorto"),
        widget=comboCargo(
            search_fields=[
                "nombrem__icontains"
            ],
            max_results=10
        )
    )

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "persona", "cargo"
        ]


class FormIntegranteCambiar(AppBaseModelForm):
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            data_view="appini:persona_listar",
            search_fields=[
                "apellidocompleto__icontains",
                "numero__startswith"
            ]
        )
    )
    documentoanio = forms.ChoiceField(
        label="Año",
        choices=[],
        required=True
    )
    documentooficina = forms.ModelChoiceField(
        label="Oficina",
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

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "persona", "documentoanio", "documentooficina",
            "documentotipo", "documentosustento"
        ]

    def __init__(self, *args, **kwargs):
        super(FormIntegranteCambiar, self).__init__(*args, **kwargs)
        self.fields["documentoanio"].choices = [
            (anio, anio) for anio in
            range(datetime.datetime.now().year, settings.CONFIG_APP["AnioInicio"] - 1, -1)
        ]


class FormPresidenteAprobar(AppBaseModelForm):
    oculto = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "oculto"
        ]

    def clean(self):
        # Al presidente actual le damos de baja
        presidenteActual = self.instance.area.jefeactual
        presidenteActual.activo = False
        presidenteActual.fin = timezone.now()
        presidenteActual.save()
        areaActual = presidenteActual.area
        areaActual.jefeactual = None
        areaActual.save()
        return super(FormPresidenteAprobar, self).clean()
