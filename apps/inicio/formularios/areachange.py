"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django_select2.forms import ModelSelect2Widget

from apps.organizacion.models import PeriodoTrabajo
from modulos.utiles.clases.formularios import AppBaseForm


class comboTrabajoArea(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.area.nombre, obj.Cargo())


class AreaChangeForm(AppBaseForm, forms.Form):
    areanueva = forms.ModelChoiceField(
        label="Unidad de Organización/Comisión",
        queryset=PeriodoTrabajo.objects.none(),
        widget=comboTrabajoArea(
            search_fields=["area__nombre__icontains"],
            max_results=10,
            data_view="appini:area_change_listar"
        )
    )
