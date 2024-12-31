"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.db.models import Q
from django_select2.forms import Select2Widget

from apps.organizacion.models import Area, PeriodoTrabajo, DocumentoTipoArea, TrabajadoresActuales
from apps.tramite.models import Documento, Expediente
from apps.tramite.vistas.bandejas import QueryOficinaBandejaEmitidos
from modulos.select2.widgetselect2 import MADModelSelect2Widget
from modulos.utiles.clases.campos import AppInputNumber, TextAreaAutoWidget, CheckWidget
from modulos.utiles.clases.formularios import AppBaseModelForm, AppBaseForm


class comboFirmador(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.persona.apellidocompleto


class comboTipoDocumento(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.documentotipo.nombre


class DocumentoEmitirForm(AppBaseModelForm):
    expediente = forms.ModelChoiceField(
        label="Expediente",
        queryset=Expediente.objects.none()
    )
    arearesponsable = forms.ModelChoiceField(
        label="Firmado en",
        queryset=Area.objects.all(),
        widget=MADModelSelect2Widget(
            search_fields=[
                "nombre__icontains"
            ],
            max_results=10
        )
    )
    responsable = forms.ModelChoiceField(
        label="Firmado por",
        queryset=PeriodoTrabajo.objects.none(),
        widget=comboFirmador(
            search_fields=[
                "persona__apellidocompleto__icontains"
            ],
            max_results=10,
            dependent_fields={"arearesponsable": "area"},
            data_view="apptra:documento_responsable_listar"
        )
    )
    documentotipoarea = forms.ModelChoiceField(
        label="Tipo de Documento",
        queryset=DocumentoTipoArea.objects.none(),
        widget=comboTipoDocumento(
            search_fields=["documentotipo__nombre__icontains"],
            max_results=10,
            dependent_fields={"arearesponsable": "area"},
            data_view="apptra:documento_tipo_listar"
        )
    )
    forma = forms.ChoiceField(
        choices=Documento.FORMAS,
        required=False
    )
    destinos = forms.CharField(
        error_messages={"required": "Debe indicar almenos un destino"},
        required=True,
        widget=forms.HiddenInput()
    )
    firmas = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    anexos = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    referencias = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    atenciones = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Documento
        fields = [
            "expediente", "arearesponsable", "responsable", "documentotipoarea", "anexos", "asunto",
            "destinos", "firmas", "referencias", "confidencial", "forma", "atenciones"
        ]

    def __init__(self, *args, **kwargs):
        super(DocumentoEmitirForm, self).__init__(*args, **kwargs)
        self.fields["responsable"].queryset = TrabajadoresActuales().filter(
            Q(esjefe=True)
            |
            Q(tipo__in=["EN", "EP"])
            |
            Q(area__paracomisiones=True, tipo="NN", cargo__esprincipal=True)
        ).order_by("persona__apellidocompleto")
        self.fields["asunto"].widget = TextAreaAutoWidget()
        self.fields["confidencial"].widget = CheckWidget(
            ontext="<i class='fas fa-lock text-white fa-1x mr-1'></i> Si",
            offtext="No",
            oncolor="danger",
            offcolor="primary"
        )
        self.fields["expediente"].empty_label = "-" * 5


class DocumentoEstadoForm(AppBaseModelForm):
    codest = forms.CharField(max_length=2, widget=forms.HiddenInput())
    modoest = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Documento
        fields = ["codest", "modoest"]


class DocumentoObservarForm(AppBaseModelForm):
    observacion = forms.CharField(
        label="Observación",
        required=True,
        widget=forms.Textarea
    )

    firstfield = "observacion"

    class Meta:
        model = Documento
        fields = ["observacion"]


class DocumentoAnularForm(AppBaseModelForm):
    codest = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Documento
        fields = ["codest"]


class DocumentoEmitirFirmaVBObservarForm(AppBaseModelForm):
    observacion = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Motivo de la Observación"}
        )
    )
    firstfield = "observacion"

    class Meta:
        model = Documento
        fields = ["observacion"]


class DocumentoEmitirCambiarResponsableForm(AppBaseModelForm):
    nuevoresponsable = forms.ModelChoiceField(
        queryset=PeriodoTrabajo.objects.none(),
        label="Nuevo Responsable",
        required=True,
        widget=MADModelSelect2Widget(
            search_fields=["persona__apellidocompleto"],
            max_results=10
        )
    )

    class Meta:
        model = Documento
        fields = ["nuevoresponsable"]

    def __init__(self, *args, **kwargs):
        super(DocumentoEmitirCambiarResponsableForm, self).__init__(*args, **kwargs)
        # self.fields["nuevoresponsable"].queryset = TrabajadoresActuales().filter(
        #     Q(esjefe=True)
        #     |
        #     Q(tipo__in=["EN", "EP"])
        #     |
        #     Q(area__paracomisiones=True, tipo="NN", cargo__esprincipal=True)
        # ).order_by("persona__apellidocompleto")


class comboOficinaEmitidos(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.siglas, obj.nombre)


class FormOficinaEmitidos(AppBaseForm, forms.Form):
    cbofiorigen = forms.ChoiceField(
        choices=[],
        widget=Select2Widget()
    )

    def __init__(self, request, *args, **kwargs):
        super(FormOficinaEmitidos, self).__init__(*args, **kwargs)
        oficinas = [(0, "TODOS")]
        for area in Area.objects.filter(
                pk__in=QueryOficinaBandejaEmitidos(request).values("responsable__area__id")
        ).order_by("siglas"):
            oficinas.append((area.pk, "%s - %s" % (area.nombrecorto, area.nombre)))
        self.fields["cbofiorigen"].choices = oficinas
