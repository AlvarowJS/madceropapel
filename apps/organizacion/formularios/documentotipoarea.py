"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.conf import settings
from django.forms import ModelMultipleChoiceField

from apps.organizacion.models import Area, Dependencia
from apps.tramite.models import DocumentoTipo
from modulos.select2.widgetselect2 import MADModelSelect2Widget, MADModelSelect2MultipleWidget
from modulos.utiles.clases.formularios import AppBaseForm, AppBaseModelForm


class FormDocumentoTipoAreaSelector(AppBaseForm, forms.Form):
    cbtdep = forms.ChoiceField(
        label="Dependencia",
        choices=[]
    )
    cbtarea = forms.ModelChoiceField(
        label="Unidad Organizacional",
        queryset=Area.objects.filter(
            # paracomisiones=False,
            activo=True
        ).order_by("nombre"),
        widget=MADModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10,
            data_view="apporg:documentotipoarea_areas_listar",
            dependent_fields={"cbtdep": "padre"}
        )
    )

    def __init__(self, *args, **kwargs):
        super(FormDocumentoTipoAreaSelector, self).__init__(*args, **kwargs)
        dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
        dependencias = [(dependencia.codigo, dependencia.nombre.upper())]
        for rindente in Area.objects.filter(activo=True, paracomisiones=False, esrindente=True).order_by("nombre"):
            dependencias.append(
                (rindente.pk, rindente.nombre)
            )
        self.fields["cbtdep"].choices = dependencias


class FormDocumentoTipoArea(AppBaseModelForm):
    tiposdocumentos = ModelMultipleChoiceField(
        label="Tipos de Documentos",
        queryset=DocumentoTipo.objects.order_by("nombre"),
        required=True,
        widget=MADModelSelect2MultipleWidget(
            search_fields=["nombre__icontains"],
            max_results=10
        ),
        error_messages={"required": "Debe seleccionar al menos un tipo de documento"}
    )

    class Meta:
        model = DocumentoTipo
        fields = ["tiposdocumentos"]
