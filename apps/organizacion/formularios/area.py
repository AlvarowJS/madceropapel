"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.conf import settings
from django_select2.forms import ModelSelect2Widget, ModelSelect2MultipleWidget

from apps.inicio.models import Distrito, Cargo
from apps.organizacion.models import Area, AreaTipo, Dependencia
from apps.tramite.formularios.mesapartesregistrar import comboDistritoFull
from modulos.utiles.clases.campos import CheckWidget, WidgetHora
from modulos.utiles.clases.formularios import AppBaseModelForm


class comboCargoOficial(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.nombrem


class FormArea(AppBaseModelForm):
    areatipo = forms.ModelChoiceField(
        queryset=AreaTipo.objects.filter(paracomision=False).order_by("nombre")
    )
    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.order_by(
            "provincia__departamento__nombre",
            "provincia__nombre",
            "nombre",
        ),
        widget=comboDistritoFull(
            max_results=10,
            search_fields=[
                "nombre__icontains",
            ]
        )
    )
    cargooficial = forms.ModelChoiceField(
        required=True,
        queryset=Cargo.objects.order_by("nombrem"),
        widget=comboCargoOficial(
            max_results=10,
            search_fields=["nombrem__icontains"]
        )
    )
    firstfield = "nombre"
    mensajeriadistritosl = forms.ModelMultipleChoiceField(
        label="Distritos de Mensajería",
        required=False,
        queryset=Distrito.objects.order_by("nombre"),
        widget=ModelSelect2MultipleWidget(
            search_fields=["nombre__icontains"],
            max_results=10
        )
    )

    class Meta:
        model = Area
        fields = [
            "nombre", "nombrecorto", "siglas", "mesadepartes", "areatipo", "esrindente",
            "distrito", "direccion", "telefono", "web", "nivel", "cargooficial",
            "mensajeria", "mensajeriaambito", "mensajeriadistritosl",
            "mensajeriahoramaxima", "firmamargensuperior"
        ]

    def __init__(self, *args, **kwargs):
        super(FormArea, self).__init__(*args, **kwargs)
        if not self.instance.pk or not self.instance.esrindente:
            del self.fields["distrito"]
            del self.fields["direccion"]
            del self.fields["telefono"]
            del self.fields["web"]
        if not self.instance.mensajeria:
            del self.fields["mensajeriahoramaxima"]
        else:
            self.fields["mensajeriahoramaxima"].widget = WidgetHora()
        self.fields["mensajeriadistritosl"].queryset = self.fields["mensajeriadistritosl"].queryset.filter(
            provincia=Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]).ubigeo.provincia
        )
        self.fields["esrindente"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
        self.fields["mesadepartes"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
        self.fields["mensajeria"].widget = CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )


class FormAreaActivar(AppBaseModelForm):
    oculto = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Area
        fields = ["oculto"]


class FormAreaMover(AppBaseModelForm):
    apadre = forms.IntegerField()
    aposicion = forms.IntegerField()

    class Meta:
        model = Area
        fields = [
            "apadre", "aposicion"
        ]
