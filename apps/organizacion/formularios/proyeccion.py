"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms import ModelMultipleChoiceField
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.organizacion.models import Proyeccion, PeriodoTrabajo, Area
from modulos.select2.widgetselect2 import MADModelSelect2Widget, MADModelSelect2MultipleWidget
from modulos.utiles.clases.formularios import AppBaseForm, AppBaseModelForm


class comboProyeccionTrabajador(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - %s - %s" % (
            obj.persona.apellidocompleto,
            obj.area.nombre,
            obj.Cargo(),
            obj.get_tipo_display()
        )


class FormProyeccionTrabajadorSelector(AppBaseForm, forms.Form):
    cbtrabajador = forms.ModelChoiceField(
        label="Trabajador",
        queryset=PeriodoTrabajo.objects.filter(
            activo=True,
            inicio__lte=timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        ).filter(
            Q(fin__gt=timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE)))
            |
            Q(fin__isnull=True)
        ).order_by("persona__nombrecompleto"),
        widget=comboProyeccionTrabajador(
            search_fields=[
                "persona__apellidocompleto__icontains",
                "persona__numero__icontains",
                "area__nombre__icontains",
                "area__siglas__icontains",
            ],
            max_results=10
        )
    )

    def __init__(self, *args, **kwargs):
        super(FormProyeccionTrabajadorSelector, self).__init__(*args, **kwargs)
        # fechaActual = timezone.localdate(timezone.now())
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        self.fields["cbtrabajador"].queryset = self.fields["cbtrabajador"].queryset.filter(
            Q(inicio__lte=fechaActual, fin=None)
            |
            Q(inicio__lte=fechaActual, fin__gte=fechaActual)
        )


class FormProyeccion(AppBaseModelForm):
    areasorigen = ModelMultipleChoiceField(
        label="Unidades de Organización de Origen",
        queryset=Area.objects.filter(activo=True).exclude(codigo="0" * 5).order_by("nombre"),
        required=True,
        widget=MADModelSelect2MultipleWidget(
            search_fields=["nombre__icontains"],
            max_results=10
        ),
        error_messages={"required": "Debe seleccionar al menos una unidad organizacional"}
    )

    class Meta:
        model = Proyeccion
        fields = ["areasorigen"]


class FormProyeccionArea(AppBaseModelForm):
    trabajadores = ModelMultipleChoiceField(
        label="Trabajadores",
        queryset=PeriodoTrabajo.objects.filter(
            activo=True, area__paracomisiones=False
        ).order_by("persona__apellidocompleto"),
        required=True,
        widget=MADModelSelect2MultipleWidget(
            search_fields=["persona__apellidocompleto__icontains"],
            max_results=10
        ),
        error_messages={"required": "Debe seleccionar al menos un trabajador"}
    )

    class Meta:
        model = Proyeccion
        fields = ["trabajadores"]
