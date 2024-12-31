"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.conf import settings

from apps.organizacion.formularios.apoyo import comboDocumentoTipo
from apps.organizacion.models import Area, Dependencia, DocumentoTipoArea
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.formularios import AppBaseForm, AppBaseModelForm


class FormCorrelativoSelector(AppBaseForm, forms.Form):
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
    cbttipodoc = forms.ModelChoiceField(
        label="Tipo de Documento",
        queryset=DocumentoTipoArea.objects.order_by("documentotipo__nombre"),
        widget=comboDocumentoTipo(
            search_fields=["documentotipo__nombre__icontains"],
            max_results=10,
            dependent_fields={"cbtarea": "area"}
        )
    )

    def __init__(self, *args, **kwargs):
        super(FormCorrelativoSelector, self).__init__(*args, **kwargs)
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


class FormCorrelativo(AppBaseModelForm):
    class Meta:
        model = DocumentoTipoArea
        fields = ["correlativo"]

    def __init__(self, *args, **kwargs):
        super(FormCorrelativo, self).__init__(*args, **kwargs)
        self.fields["correlativo"].label = "Último Número"
