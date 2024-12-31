"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django import forms
from django.conf import settings
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.inicio.models import Persona, Cargo
from apps.organizacion.models import PeriodoTrabajo, Area, Dependencia
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.campos import AppInputTextWidget, WidgetFecha, CheckWidget
from modulos.utiles.clases.formularios import AppBaseModelForm, AppBaseForm


class FormTrabajadorSelector(AppBaseForm, forms.Form):
    chktodos = forms.BooleanField(
        label="Todos",
        initial=False,
        required=False,
        widget=CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
    )
    cbtdep = forms.ChoiceField(
        label="Dependencia",
        choices=[],
    )
    cbtarea = forms.ModelChoiceField(
        label="Unidad de Organización",
        queryset=Area.objects.filter(activo=True, paracomisiones=False).order_by("nombre"),
        widget=MADModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10,
            data_view="apporg:trabajador_area_listar"
        )
    )

    def __init__(self, *args, **kwargs):
        super(FormTrabajadorSelector, self).__init__(*args, **kwargs)
        dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
        dependencias = [(dependencia.codigo, dependencia.nombre.upper())]
        for rindente in Area.objects.filter(activo=True, paracomisiones=False, esrindente=True).order_by("nombre"):
            dependencias.append(
                (rindente.pk, rindente.nombre)
            )
        if len(dependencias) > 1:
            self.fields["cbtdep"].choices = dependencias
            self.fields["cbtarea"].widget.dependent_fields = {"cbtdep": "padre"}
        else:
            del self.fields["cbtdep"]
            self.fields["cbtarea"].initial = self.fields["cbtarea"].queryset.first()


class comboPersona(MADModelSelect2Widget):
    search_fields = [
        "apellidocompleto__icontains",
        "numero__startswith"
    ]
    max_results = 10

    def label_from_instance(self, obj):
        return "%s" % obj.apellidocompleto


class comboCargo(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return obj.nombrem


class FormPeriodoTrabajo(AppBaseModelForm):
    personadni = forms.CharField(
        label="DNI",
        max_length=8,
        min_length=8,
        widget=AppInputTextWidget(
            mask="9" * 8
        )
    )
    persona = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=comboPersona(
            data_view="appini:persona_listar"
        )
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.filter(paraunidad=True).order_by("nombrecorto"),
        widget=comboCargo(
            search_fields=[
                "nombrem__icontains"
            ],
            max_results=10
        )
    )
    usuariodominio = forms.CharField(
        label="Usuario de Dominio",
        required=False
    )
    correoinstitucional = forms.EmailField(
        label="Correo Institucional",
        required=False
    )
    permisotramite = forms.ChoiceField(
        choices=PeriodoTrabajo.PERMISOTRAMITE,
        initial="O"
    )
    # fin = forms.DateField(
    #     required=False,
    #     widget=WidgetFecha(
    #         type="date",
    #         format="DD/MM/YYYY",
    #         input_formats=["%d/%m/%Y"],
    #         mindate=timezone.now()
    #     )
    # )
    firstfield = "personadni"

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "persona", "cargo", "poscargo", "esapoyo", "permisotramite", "esjefemodo",
            "emiteexterno", "seguimientocompleto", "esmensajero"
        ]

    def __init__(self, *args, **kwargs):
        super(FormPeriodoTrabajo, self).__init__(*args, **kwargs)
        self.fields["esapoyo"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
        self.fields["emiteexterno"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
        self.fields["seguimientocompleto"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
        self.fields["esmensajero"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )

    def clean(self):
        cl = super(FormPeriodoTrabajo, self).clean()
        if not self.instance.pk:
            # self.instance.inicio = timezone.now().astimezone(tz=pytz_timezone(settings.TIME_ZONE))
            self.instance.inicio = timezone.make_aware(
                datetime.datetime.combine(
                    datetime.datetime.now().date(),
                    datetime.datetime.min.time()
                )
            )
        return cl


class FormPeriodoTrabajoPassword(AppBaseForm, forms.Form):
    oculto = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )


class FormPeriodoTrabajoRotar(AppBaseModelForm):
    cbdep = forms.ChoiceField(
        label="Dependencia",
        choices=[],
    )
    area = forms.ModelChoiceField(
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
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.filter(paraunidad=True).order_by("nombrecorto"),
        widget=comboCargo(
            search_fields=[
                "nombrem__icontains"
            ],
            max_results=10
        )
    )
    permisotramite = forms.ChoiceField(
        choices=PeriodoTrabajo.PERMISOTRAMITE,
        initial="O"
    )
    fin = forms.DateField(
        required=False,
        widget=WidgetFecha(
            type="date",
            format="DD/MM/YYYY",
            input_formats=["%d/%m/%Y"],
            mindate=timezone.now()
        )
    )
    firstfield = "personadni"

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "fin", "cargo", "poscargo", "esapoyo", "permisotramite", "esjefemodo"
        ]

    def clean(self):
        cl = super(FormPeriodoTrabajoRotar, self).clean()
        self.instance.area = cl["area"]
        return cl

    def __init__(self, *args, **kwargs):
        super(FormPeriodoTrabajoRotar, self).__init__(*args, **kwargs)
        dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
        dependencias = [(dependencia.codigo, dependencia.nombre.upper())]
        for rindente in Area.objects.filter(activo=True, paracomisiones=False, esrindente=True).order_by("nombre"):
            dependencias.append(
                (rindente.pk, rindente.nombre)
            )
        self.fields["cbdep"].choices = dependencias


class FormPeriodoTrabajoBaja(AppBaseModelForm):
    oculto = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = PeriodoTrabajo
        fields = [
            "oculto"
        ]


class FormPeriodoTrabajoLogout(AppBaseModelForm):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = PeriodoTrabajo
        fields = ["oculto"]
