"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django import forms
from django.conf import settings
from django_select2.forms import Select2Widget, ModelSelect2Widget

from apps.inicio.formularios.pj import comboUbigeo
from apps.inicio.models import Distrito
from apps.tramite.models import CargoExterno, AmbitoMensajeria, Distribuidor, CargoExternoDetalle
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.campos import CheckWidget, ModelFileField
from modulos.utiles.clases.formularios import AppBaseModelForm, AppBaseForm


class FormListar(AppBaseForm, forms.Form):
    cvista = forms.ChoiceField(
        label="Listar",
        choices=[('D', 'Del día'), ('T', 'Todos')],
        required=False
    )


class FormAmbitos(AppBaseForm, forms.Form):
    ambitos = forms.ModelChoiceField(
        queryset=AmbitoMensajeria.objects.order_by("orden"),
        to_field_name="codigo"
        # widget=forms.Select(
        #     attrs={"class": "selectpicker w-100"}
        # )
    )

    def __init__(self, *args, **kwargs):
        super(FormAmbitos, self).__init__(*args, **kwargs)
        self.fields["ambitos"].empty_label = "Todos"


class comboPlanillado(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - %s" % (
            obj.Numero(),
            obj.fecha.strftime("%d/%m/%Y"),
            obj.ambito.nombre
        )


class FormDestinoPlanilladoAgregar(AppBaseModelForm):
    anio = forms.ChoiceField(
        label="Año",
        choices=[],
        required=True
    )
    planillado = forms.ModelChoiceField(
        queryset=CargoExterno.objects.order_by("-numero"),
        widget=comboPlanillado(
            search_fields=["numero"],
            max_results=10,
            dependent_fields={"anio": "anio"}
        )
    )
    distribuidortipo = forms.ChoiceField(
        label="Tipo",
        choices=Distribuidor.TIPO
    )
    distribuidor = forms.ModelChoiceField(
        queryset=Distribuidor.objects.filter(
            estado=True,
            fin__isnull=True
        ).order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=["nombre__icontains"],
            max_results=10,
            dependent_fields={
                "distribuidortipo": "tipo"
            }
        )
    )
    destinos = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    firstfield = "numero"

    class Meta:
        model = CargoExterno
        fields = [
            "ambito", "distribuidortipo", "distribuidor", "fecha", "nota"
        ]

    def __init__(self, *args, **kwargs):
        super(FormDestinoPlanilladoAgregar, self).__init__(*args, **kwargs)
        self.fields["anio"].choices = [
            (anio, anio) for anio in
            range(datetime.datetime.now().year, settings.CONFIG_APP["AnioInicio"] - 1, -1)
        ]


class FormDestinoPlanilladoRectificar(AppBaseModelForm):
    ubigeo = forms.ModelChoiceField(
        label="UBIGEO",
        queryset=Distrito.objects.order_by(
            "provincia__departamento__nombre",
            "provincia__nombre",
            "nombre"
        ),
        widget=comboUbigeo(
            search_fields=[
                "nombre__icontains",
                "provincia__nombre__icontains",
            ],
            max_results=10,
        ),
        required=False
    )
    firstfield = "direccion"

    class Meta:
        model = CargoExternoDetalle
        fields = [
            "ubigeo", "direccion", "referencia", "detalle"
        ]


class cbpsplla(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - %s" % (
            obj.NumeroFull(),
            obj.fecha.strftime("%d/%m/%Y"),
            obj.ambito.nombre
        )


class FormPllaSelector(AppBaseForm, forms.Form):
    pstodos = forms.BooleanField(
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
    psplla = forms.ModelChoiceField(
        label="N° Planillado",
        queryset=CargoExterno.objects.none(),
        widget=cbpsplla(
            search_fields=[
                "numero"
            ],
            max_results=10
        )
    )

    def __init__(self, request, *args, **kwargs):
        super(FormPllaSelector, self).__init__(*args, **kwargs)
        periodoactual = request.user.persona.periodotrabajoactual(
            request.session.get("cambioperiodo")
        )
        arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
        qs = CargoExterno.objects.filter(
            ultimoestado__estado__in=["GN", "CE"]
        ).order_by("-anio", "-numero")
        if arearindente:
            qs = qs.filter(emisorarearindente=arearindente)
        else:
            qs = qs.filter(emisorarearindente__isnull=True)
        self.fields["psplla"].queryset = qs
        self.fields["psplla"].initial = qs.first()


class FormPllaSelectorF(AppBaseForm, forms.Form):
    pstodos = forms.BooleanField(
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
    psplla = forms.ModelChoiceField(
        label="N° Planillado",
        queryset=CargoExterno.objects.none(),
        widget=cbpsplla(
            search_fields=[
                "numero"
            ],
            max_results=10
        )
    )

    def __init__(self, request, *args, **kwargs):
        super(FormPllaSelectorF, self).__init__(*args, **kwargs)
        periodoactual = request.user.persona.periodotrabajoactual(
            request.session.get("cambioperiodo")
        )
        arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
        qs = CargoExterno.objects.filter(
            ultimoestado__estado__in=["FI", "FD"]
        ).order_by("-anio", "-numero")
        if arearindente:
            qs = qs.filter(emisorarearindente=arearindente)
        else:
            qs = qs.filter(emisorarearindente__isnull=True)
        self.fields["psplla"].queryset = qs
        self.fields["psplla"].initial = qs.first()


class FormDestinoPlanilladoEnviar(AppBaseModelForm):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = CargoExterno
        fields = ["oculto"]


class FormDestinoPlanilladoFinalizar(AppBaseModelForm):
    oculto = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = CargoExterno
        fields = ["oculto"]


class FormDestinoPlanilladoCargo(AppBaseModelForm):
    destinos = forms.CharField(widget=forms.HiddenInput())
    cargoarchivo = ModelFileField(
        label="Archivo",
        required=True,
        maxsize=1024 * 20,
        extensiones=["pdf"]
    )

    class Meta:
        model = CargoExterno
        fields = ["destinos", "cargoarchivo", "cargofecha", "cargoobservacion"]

    def __init__(self, *args, **kwargs):
        super(FormDestinoPlanilladoCargo, self).__init__(*args, **kwargs)
        self.fields["cargofecha"].widget.attrs["data-sidebyside"] = "true"
        self.fields["cargofecha"].required = True
