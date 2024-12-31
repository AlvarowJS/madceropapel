"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import forms
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_select2.forms import HeavySelect2Widget, ModelSelect2Widget

from apps.inicio.models import Departamento, Provincia, Distrito, PersonaJuridica, Persona, Cargo
from apps.organizacion.models import Area, PeriodoTrabajo, Dependencia, DocumentoTipoArea, TrabajadoresActuales
from apps.tramite.models import Destino, TipoTramite, DocumentoFirma, DocumentoReferencia, DocumentoReferenciaOrigen, \
    DocumentoReferenciaModo, TipoProveido, Anexo, AnexoFirma, Documento, MensajeriaModoEntrega
from apps.tramite.vistas.varios import ConsultarDNI
from modulos.select2.widgetselect2 import MADModelSelect2Widget, SGDModelSelect2Widget, MADNucleoModelSelect2Widget
from modulos.utiles.clases.campos import AppInputTextWidget, RadioSelectWidget, AppInputNumber, ModelFileField, \
    TextAreaAutoWidget, CheckWidget
from modulos.utiles.clases.formularios import AppBaseModelForm


class comboPersona(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.persona.apellidocompleto


class comboDependencia(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.nombre


class comboUbigeo(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return obj.RutaDepartamento()


class comboModoEntrega(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "<i class='%s text-%s mr-2'></i>%s" % (
            obj.icono,
            obj.color,
            obj.nombre
        )


class FormDestino(AppBaseModelForm):
    cargonombre = forms.CharField(
        widget=forms.HiddenInput(),
        initial="",
        required=False
    )
    dependenciasiglas = forms.CharField(
        widget=forms.HiddenInput(),
        initial="",
        required=False
    )
    codigo = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    ubigeo = forms.ModelChoiceField(
        label="UBIGEO",
        queryset=Distrito.objects.order_by(
            "provincia__departamento__nombre",
            "provincia__nombre",
            "nombre"
        ),
        widget=comboUbigeo(
            search_fields=[
                "nombre__icontains"
            ],
            max_results=10,
        )
    )
    tipodestinatario = forms.CharField(
        max_length=2, widget=forms.HiddenInput
    )
    dep = forms.ChoiceField(
        label="Dependencia",
        choices=[],
        required=False
    )
    area = forms.ModelChoiceField(
        label="Unidad Organizacional",
        queryset=Area.objects.filter(
            activo=True  # , paracomisiones=False
        ).order_by("nombre"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "nombre__icontains",
                "siglas__icontains",
            ],
            data_view="apptra:documento_destino_uo_listar",
            dependent_fields={"dep": "padre"}
        )
    )
    periodotrabajo = forms.ModelChoiceField(
        queryset=PeriodoTrabajo.objects.none(),
        widget=comboPersona(
            max_results=10,
            search_fields=[
                "persona__apellidocompleto__icontains"
            ],
            dependent_fields={"area": "area"},
            data_view="apptra:documento_destino_pt_listar"
        )
    )
    personadni = forms.CharField(
        label="DNI",
        min_length=8,
        max_length=8,
        widget=AppInputTextWidget(
            mask="9" * 8
        )
    )
    persona = forms.ModelChoiceField(
        required=False,
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "numero__startswith",
                "apellidocompleto__icontains"
            ],
            data_view="appini:persona_listar"
        )
    )
    personajuridicatipo = forms.ChoiceField(
        required=False,
        label="Tipo",
        choices=Documento.PERSONAJURIDICATIPO,
        initial=Documento.PERSONAJURIDICATIPO[0][0]
    )
    personajuridicaruc = forms.CharField(
        label="RUC",
        min_length=11,
        max_length=11,
        widget=AppInputTextWidget(
            mask="9" * 11
        ),
        required=False
    )
    personajuridica = forms.ModelChoiceField(
        queryset=PersonaJuridica.objects.order_by("razoncomercial"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "ruc__startswith",
                "razoncomercial__icontains"
            ],
            data_view="appini:personajuridica_listar"
        ),
        required=False
    )
    personajuridicarz = forms.ModelChoiceField(
        label="Otra Entidad Externa",
        queryset=PersonaJuridica.objects.filter(tipo="O").order_by("razoncomercial"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "ruc__startswith",
                "razoncomercial__icontains"
            ],
            data_view="appini:personajuridicarz_listar"
        ),
        required=False
    )
    tipotramite = forms.ModelChoiceField(
        queryset=TipoTramite.objects.filter(duenio="O").order_by("nombre")
    )
    proveido = forms.ModelChoiceField(
        queryset=TipoProveido.objects.filter(estado=True).order_by("nombre"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "nombre__icontains"
            ]
        )
    )
    dependencia = forms.ModelChoiceField(
        queryset=Dependencia.objects.exclude(codigo=settings.CONFIG_APP["Dependencia"]).order_by("nombre"),
        widget=comboDependencia(
            max_results=10,
            search_fields=[
                "nombre__icontains"
            ],
            data_view="apptra:documento_ref_dep_listar"
        )
    )
    dependencia_area = forms.CharField(
        widget=HeavySelect2Widget(
            data_url="%s%s" % (
                settings.CONFIG_APP["NUCLEO"]["URL"],
                settings.CONFIG_APP["NUCLEO"]["MAD3"]["areas"]["listar"]
            ),
            dependent_fields={"dependencia": "dependencia"},
            max_results=10,
            search_fields=[
                "nombre__icontains"
            ]
        ),
        required=True
    )
    dependencia_area_prechoices = None
    dependencia_responsable_texto = forms.CharField(
        label="Responsable",
        required=False,
        # widget=forms.Textarea()
    )
    dependencia_responsable_dni = forms.CharField(
        widget=forms.HiddenInput()
    )
    dependencia_responsable_cargo = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    tieneentregafisica = forms.BooleanField(
        initial=False,
        label="¿Adjuntar información física?",
        required=False,
        widget=CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
    )
    obsnew = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    mensajeriamodoentrega = forms.ModelChoiceField(
        queryset=MensajeriaModoEntrega.objects.filter(estado=True).order_by("orden"),
        widget=comboModoEntrega(
            max_results=10,
            search_fields=["nombre__icontains"]
        )
    )

    class Meta:
        model = Destino
        fields = [
            "tipodestinatario", "area", "periodotrabajo", "personajuridica", "personajuridicatipo",
            "personajuridicaruc", "personajuridicarz", "persona", "tipotramite", "proveido", "indicacion",
            "ubigeo", "direccion", "referencia", "correo", "codigo", "personacargo",
            "dependencia", "dependencia_area", "dependencia_responsable_texto",
            "dependencia_responsable_dni", "dependencia_responsable_cargo",
            "dependencia_area_nombre", "entregafisica", "diasatencion", "tieneentregafisica",
            "obsnew", "mensajeriamodoentrega"
        ]
        widgets = {
            "indicacion": TextAreaAutoWidget(),
            "entregafisica": TextAreaAutoWidget()
        }

    def __init__(self, request, *args, **kwargs):
        if "dependencia_area_prechoices" in kwargs:
            self.dependencia_area_prechoices = kwargs.pop("dependencia_area_prechoices")
        super(FormDestino, self).__init__(*args, **kwargs)
        self.request = request
        tipodest = self.data["tipodestinatario"]
        self.fields["periodotrabajo"].queryset = TrabajadoresActuales()
        self.fields["mensajeriamodoentrega"].required = False
        self.fields["personacargo"].widget.attrs["typeahead"] = reverse("apptra:documento_destinos_cargos")
        if tipodest == "UO":
            del self.fields["personajuridicaruc"]
            del self.fields["personajuridica"]
            del self.fields["personajuridicarz"]
            del self.fields["personajuridicatipo"]
            del self.fields["personadni"]
            del self.fields["persona"]
            del self.fields["personacargo"]
            del self.fields["ubigeo"]
            del self.fields["direccion"]
            del self.fields["referencia"]
            del self.fields["correo"]
            del self.fields["dependencia"]
            del self.fields["dependencia_area"]
            del self.fields["dependencia_area_nombre"]
            del self.fields["dependencia_responsable_texto"]
            del self.fields["dependencia_responsable_dni"]
            del self.fields["dependencia_responsable_cargo"]
            del self.fields["mensajeriamodoentrega"]
            dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
            dependencias = [(dependencia.codigo, dependencia.nombre.upper())]
            for rindente in Area.objects.filter(activo=True, paracomisiones=False, esrindente=True).order_by("nombre"):
                dependencias.append(
                    (rindente.pk, rindente.nombre)
                )
            self.fields["dep"].choices = dependencias
        elif tipodest == "DP":
            del self.fields["personajuridicarz"]
            del self.fields["personajuridicatipo"]
            del self.fields["personajuridicaruc"]
            del self.fields["personajuridica"]
            del self.fields["personadni"]
            del self.fields["persona"]
            del self.fields["personacargo"]
            del self.fields["ubigeo"]
            del self.fields["direccion"]
            del self.fields["referencia"]
            del self.fields["correo"]
            del self.fields["dep"]
            del self.fields["area"]
            del self.fields["periodotrabajo"]
            del self.fields["mensajeriamodoentrega"]
            if self.dependencia_area_prechoices:
                self.fields["dependencia_area"].widget.choices = self.dependencia_area_prechoices
                self.fields["dependencia_area"].initial = self.data["dependencia_area"]
            self.fields["dependencia_responsable_texto"].widget.attrs["readonly"] = True
            self.fields["dependencia_responsable_texto"].widget.attrs["style"] = "background-color: #F3F6F9"
        elif tipodest == "PJ":
            del self.fields["dep"]
            del self.fields["area"]
            del self.fields["periodotrabajo"]
            del self.fields["diasatencion"]
            del self.fields["dependencia"]
            del self.fields["dependencia_area"]
            del self.fields["dependencia_area_nombre"]
            del self.fields["dependencia_responsable_texto"]
            del self.fields["dependencia_responsable_dni"]
            del self.fields["dependencia_responsable_cargo"]
            del self.fields["entregafisica"]
            del self.fields["tieneentregafisica"]
            self.fields["personajuridicaruc"].widget.attrs['autofocus'] = 'autofocus'
            self.fields["personadni"].required = False
            self.fields["persona"].required = False
            self.fields["direccion"].required = True
        elif tipodest == "CI":
            del self.fields["dep"]
            del self.fields["area"]
            del self.fields["periodotrabajo"]
            del self.fields["personajuridicarz"]
            del self.fields["personajuridicatipo"]
            del self.fields["personajuridicaruc"]
            del self.fields["personajuridica"]
            del self.fields["personacargo"]
            del self.fields["diasatencion"]
            del self.fields["dependencia"]
            del self.fields["dependencia_area"]
            del self.fields["dependencia_area_nombre"]
            del self.fields["dependencia_responsable_texto"]
            del self.fields["dependencia_responsable_dni"]
            del self.fields["dependencia_responsable_cargo"]
            del self.fields["entregafisica"]
            del self.fields["tieneentregafisica"]
            self.fields["personadni"].required = True
            self.fields["persona"].required = True
            self.fields["direccion"].required = True
            self.fields["personadni"].widget.attrs['autofocus'] = 'autofocus'

    def clean(self):
        cl = super(FormDestino, self).clean()
        dni = cl.get("dependencia_responsable_dni")
        if cl["tipodestinatario"] == "DP" and dni:
            persona = Persona.objects.filter(
                tipodocumentoidentidad__codigo="DNI", numero=dni
            ).first()
            if not persona:
                persona, estado = ConsultarDNI(dni, self.request)
            self.instance.dependencia_responsable = persona
            if cl.get("dependencia_responsable_cargo") and not isinstance(cl["dependencia_responsable_cargo"], Cargo):
                cl["dependencia_responsable_cargo"] = Cargo.objects.get(pk=cl["dependencia_responsable_cargo"])
        if isinstance(cl.get("personajuridicarz"), int):
            cl["personajuridicarz"] = PersonaJuridica.objects.get(pk=cl.get("personajuridicarz"))
        return cl


class FormFirma(AppBaseModelForm):
    codigo = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    area = forms.ModelChoiceField(
        label="Unidad Organizacional",
        queryset=Area.objects.filter(activo=True).order_by("nombre"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "nombre__icontains",
                "siglas__icontains",
            ],
            data_view="apptra:documento_destino_uo_listar"
        )
    )
    empleado = forms.ModelChoiceField(
        queryset=PeriodoTrabajo.objects.order_by("persona__apellidocompleto"),
        widget=comboPersona(
            max_results=10,
            search_fields=[
                "persona__apellidocompleto__icontains"
            ],
            dependent_fields={"area": "area"},
            data_view="apptra:documento_destino_pt_listar"
        )
    )
    modofirma = forms.ChoiceField(
        label="Modo",
        choices=DocumentoFirma.MODO,
        widget=RadioSelectWidget()
    )

    class Meta:
        model = DocumentoFirma
        fields = [
            "codigo", "area", "empleado", "modofirma"
        ]

    def clean(self):
        cl = super(FormFirma, self).clean()
        mf = cl.get("modofirma")
        if mf:
            self.instance.modo = cl.get("modofirma")
        return cl


class cboDocTipoMCP(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.documentotipo.nombre


class cboOrigenPerMCP(ModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s" % obj.persona.apellidocompleto


class FormReferencia(AppBaseModelForm):
    codigo = forms.IntegerField(widget=forms.HiddenInput())
    anio = forms.ChoiceField(
        choices=[(anio, anio) for anio in range(timezone.now().date().year, 2009, -1)],
        widget=forms.Select(),
        required=False
    )
    origen = forms.ModelChoiceField(
        empty_label=None,
        queryset=DocumentoReferenciaOrigen.objects.filter(
            Q(codigo__in=["MCP", "EXT"])
            |
            Q(estado=True)
        ).order_by("orden"),
        widget=RadioSelectWidget(
            attrsfields=["pideanio", "pidedependencia", "anioinicio", "tienemodos", "tienepdf", "codigo"]
        )
    )
    modoref = forms.ModelChoiceField(
        label="Modo",
        empty_label=None,
        queryset=DocumentoReferenciaModo.objects.order_by("orden"),
        widget=RadioSelectWidget(attrsfields=["pideoficina", "pidetipo", "codigo"])
    )
    numero = AppInputNumber(
        minimo=1,
        css="form-control text-center"
    )
    dependencia = forms.ModelChoiceField(
        queryset=Dependencia.objects.filter(estado=True).order_by("nombre"),
        widget=comboDependencia(
            search_fields=["nombre__icontains"],
            max_results=10,
            data_view="apptra:documento_ref_dep_listar"
        )
    )
    oficinasgd = forms.CharField(
        label="Oficina",
        widget=SGDModelSelect2Widget(
            data_url="%s%s" % (
                settings.CONFIG_APP["NUCLEO"]["URL"],
                settings.CONFIG_APP["NUCLEO"]["SGD"]["areas"]
            )
        ),
        required=False
    )
    documentotiposgd = forms.CharField(
        label="Tipo de Documento",
        widget=SGDModelSelect2Widget(
            data_url="%s%s" % (
                settings.CONFIG_APP["NUCLEO"]["URL"],
                settings.CONFIG_APP["NUCLEO"]["SGD"]["tipos"]
            )
        ),
        required=False
    )
    oficinamcp = forms.ModelChoiceField(
        label="Unidad Organizacional/Comisión",
        queryset=Area.objects.order_by("nombre"),
        widget=ModelSelect2Widget(
            search_fields=[
                "nombre__icontains",
                "siglas__icontains"
            ],
            max_results=10
        ),
        required=False
    )
    documentotipomcp = forms.ModelChoiceField(
        label="Tipo de Documento",
        queryset=DocumentoTipoArea.objects.order_by("documentotipo__nombre"),
        widget=cboDocTipoMCP(
            search_fields=[
                "documentotipo__nombre__icontains"
            ],
            max_results=10,
            dependent_fields={
                "oficinamcp": "area"
            }
        ),
        required=False
    )
    documentoorigenmcp = forms.ChoiceField(
        label="Elaborado en",
        choices=[("O", "Oficina"), ("P", "Personal")],
        initial="O",
        required=False
    )
    documentoorigenpermcp = forms.ModelChoiceField(
        label="Elaborado por",
        required=False,
        queryset=PeriodoTrabajo.objects.none(),
        widget=cboOrigenPerMCP(
            search_fields=["persona__apellidocompleto__icontains"],
            max_results=10,
            dependent_fields={"oficinamcp": "area"}
        )
    )
    refereciaexterna = forms.CharField(
        label="Referencia Externa",
        required=False,
        max_length=200
    )

    class Meta:
        model = DocumentoReferencia
        fields = [
            "codigo", "origen", "modoref", "dependencia", "anio", "numero",
            "oficinasgd", "documentotiposgd", "oficinamcp", "documentotipomcp",
            "expedientenro", "expedienteemi", "descripcion",
            "documentotiponombre", "oficinanombre", "destino",
            "refereciaexterna"
        ]
        widgets = {
            "expedientenro": forms.HiddenInput(),
            "expedienteemi": forms.HiddenInput(),
            "descripcion": forms.HiddenInput(),
            "documentotiponombre": forms.HiddenInput(),
            "oficinanombre": forms.HiddenInput(),
        }

    oficinaprechoices = None
    documentotipoprechoices = None

    def __init__(self, *args, **kwargs):
        if "oficinaprechoices" in kwargs:
            self.oficinaprechoices = kwargs.pop("oficinaprechoices")
        if "documentotipoprechoices" in kwargs:
            self.documentotipoprechoices = kwargs.pop("documentotipoprechoices")
        super(FormReferencia, self).__init__(*args, **kwargs)
        self.fields["documentoorigenpermcp"].queryset = TrabajadoresActuales().order_by("persona__apellidocompleto")
        if self.oficinaprechoices:
            self.fields["oficina"].widget.choices = self.oficinaprechoices
            self.fields["oficina"].initial = self.data["oficina"]
        if self.documentotipoprechoices:
            self.fields["documentotipo"].widget.choices = self.documentotipoprechoices
            self.fields["documentotipo"].initial = self.data["documentotipo"]
        self.fields["expedienteemi"].required = False

    def clean(self):
        cl = super(FormReferencia, self).clean()
        if cl.get("modoref"):
            self.instance.modo = cl.get("modoref")
        return cl


class FormAnexo(AppBaseModelForm):
    firmadores = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    archivof = ModelFileField(
        label="Archivo",
        required=True,
        maxsize=1024 * 20
    )

    class Meta:
        model = Anexo
        fields = [
            "descripcion", "archivof", "firmadores"
        ]

    def clean(self):
        cl = super(FormAnexo, self).clean()
        if cl.get("archivof"):
            self.instance.archivonombre = cl["archivof"].name
            self.instance.archivo = cl["archivof"].read()
        return cl


class FormAnexos(AppBaseModelForm):
    firmadores = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    archivos = ModelFileField(
        label="Carpeta",
        required=True,
        maxsize=1024 * 20,
        folder=True
    )

    class Meta:
        model = Anexo
        fields = [
            "archivos", "firmadores"
        ]


class FormAnexoImportar(AppBaseModelForm):
    listaanexos = forms.CharField(
        widget=forms.HiddenInput()
    )

    class Meta:
        model = DocumentoReferencia
        fields = [
            "listaanexos"
        ]


class AnexoFirmaEmpleado(MADModelSelect2Widget):
    def label_from_instance(self, obj):
        return "%s - %s - <span class='%s'>%s</span>" % (
            obj.persona.apellidocompleto,
            obj.area.nombre,
            "font-weight-bolder" if obj.esjefe or obj.tipo in ["EN", "EP"] else "",
            obj.Cargo()
        )


class FormAnexoFirma(AppBaseModelForm):
    codigo = forms.IntegerField(
        # required=False,
        initial=0,
        widget=forms.HiddenInput()
    )
    modo = forms.ChoiceField(
        # empty_label=None,
        choices=AnexoFirma.MODO,
        initial="VB"
    )
    empleado = forms.ModelChoiceField(
        queryset=PeriodoTrabajo.objects.none(),
        widget=AnexoFirmaEmpleado(
            search_fields=[
                "area__nombre__icontains",
                "area__siglas__icontains",
                "persona__apellidocompleto__icontains"
            ]
        )
    )

    class Meta:
        model = AnexoFirma
        fields = [
            "empleado", "modo"
        ]

    def __init__(self, *args, **kwargs):
        super(FormAnexoFirma, self).__init__(*args, **kwargs)
        self.fields["empleado"].queryset = TrabajadoresActuales().order_by("persona__apellidocompleto")
        self.fields["empleado"].widget.attrs["data-width"] = "element"


class FormDocumentoDestinoGrupo(AppBaseModelForm):
    tipotramite = forms.ModelChoiceField(
        queryset=TipoTramite.objects.filter(duenio="O").order_by("nombre")
    )
    proveido = forms.ModelChoiceField(
        queryset=TipoProveido.objects.filter(estado=True).order_by("nombre"),
        widget=MADModelSelect2Widget(
            max_results=10,
            search_fields=[
                "nombre__icontains"
            ]
        )
    )
    tieneentregafisica = forms.BooleanField(
        initial=False,
        label="¿Adjuntar información física?",
        required=False,
        widget=CheckWidget(
            ontext="Si",
            offtext="No",
            oncolor="primary",
            offcolor="warning"
        )
    )
    firstfield = "indicacion"

    class Meta:
        model = Destino
        fields = [
            "tipotramite", "proveido", "diasatencion", "indicacion",
            "tieneentregafisica", "entregafisica"
        ]
        widgets = {
            "indicacion": TextAreaAutoWidget(),
            "entregafisica": TextAreaAutoWidget()
        }
