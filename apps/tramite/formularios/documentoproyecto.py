"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django_select2.forms import Select2Widget

from apps.organizacion.models import Area
from apps.tramite.vistas.bandejas import QueryOficinaBandejaEnProyecto
from modulos.utiles.clases.formularios import AppBaseForm


class FormTablaOficinaEnProyecto(AppBaseForm, forms.Form):
    cbmodo = forms.ChoiceField(
        choices=[("PY", "En Proyecto"), ("AN", "Anulados"), ("T", "Todos")],
        initial="PY"
    )
    cbofiorigen = forms.ChoiceField(
        choices=[],
        widget=Select2Widget()
    )

    def __init__(self, request, *args, **kwargs):
        super(FormTablaOficinaEnProyecto, self).__init__(*args, **kwargs)
        oficinas = [(0, "TODOS")]
        for area in Area.objects.filter(
                pk__in=QueryOficinaBandejaEnProyecto(request).values("responsable__area__id")
        ).order_by("siglas"):
            oficinas.append((area.pk, "%s - %s" % (area.nombrecorto, area.nombre)))
        self.fields["cbofiorigen"].choices = oficinas


class FormTablaPersonalEnProyecto(AppBaseForm, forms.Form):
    cbmodo = forms.ChoiceField(
        choices=[("PY", "En Proyecto"), ("AN", "Anulados"), ("T", "Todos")],
        initial="PY"
    )
