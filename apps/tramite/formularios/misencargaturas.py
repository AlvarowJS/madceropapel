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


class comboEncargos(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - %s - %s" % (
            obj.area.nombrecorto,
            obj.inicio.strftime("%d/%m/%Y"),
            obj.fin.strftime("%d/%m/%Y"),
            obj.Cargo()
        )


class FormEncargatura(AppBaseForm, forms.Form):
    cbperiodos = forms.ModelChoiceField(
        label="Encargatura",
        queryset=PeriodoTrabajo.objects.none(),
        widget=comboEncargos(
            search_fields=[
                "cargo__nombrem",
                "area__nombre"
            ],
            max_results=10
        )
    )

    def __init__(self, request, *args, **kwargs):
        super(FormEncargatura, self).__init__(*args, **kwargs)
        self.fields["cbperiodos"].queryset = request.user.persona.Encargaturas().order_by("-inicio")
        self.fields["cbperiodos"].initial = self.fields["cbperiodos"].queryset.first()
