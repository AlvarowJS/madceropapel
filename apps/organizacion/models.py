"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q, Case, When, Value, F
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.inicio.models import TipoFirma, Cargo, Persona, Distrito
from apps.organizacion.managers import AMPeriodoTrabajo, AMArea, AMAreaNormal
from modulos.utiles.clases.formularios import Auditoria
from modulos.utiles.clases.varios import FileDimensionValidator


class Dependencia(Auditoria):
    def selloPath(self, filename):
        return '%s/firmas/%s' % (self.codigo, filename)

    principal = models.BooleanField(default=False, verbose_name="Principal")
    orden = models.IntegerField(verbose_name="Orden")
    codigo = models.CharField(max_length=6, verbose_name="Código")
    nombre = models.CharField(max_length=250, verbose_name="Nombre")
    nombrecorto = models.CharField(max_length=50, verbose_name="Nombre Corto")
    siglas = models.CharField(max_length=20, verbose_name="Siglas")
    direccion = models.CharField(max_length=250, verbose_name="Dirección")
    ubigeo = models.ForeignKey(Distrito, on_delete=models.PROTECT, verbose_name="Ubigeo")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono", null=True, blank=True)
    correo = models.EmailField(verbose_name="Correo", null=True, blank=True)
    web = models.URLField(verbose_name="Página Web", null=True, blank=True)
    ruc = models.CharField(max_length=11, verbose_name="RUC", null=True, blank=True)
    rucfirma = models.CharField(max_length=11, verbose_name="Ruc para Firma", null=True, blank=True)
    padre = models.ForeignKey(
        "self", verbose_name="Padre", related_name="hijas", on_delete=models.PROTECT, null=True, blank=True
    )
    titulodoc1 = models.CharField(max_length=200, verbose_name="Título Documento", default="")
    titulodoc2 = models.CharField(max_length=200, verbose_name="Sub Título Documento", default="")
    usaniveles = models.BooleanField(default=False, verbose_name="Usa Niveles")
    estado = models.BooleanField(default=True, verbose_name="Estado", null=True, blank=True)
    sello_firmagrc = models.BooleanField(default=False, verbose_name="Usar sello interno del Firmador")
    sello_firma = models.ImageField(
        null=True, blank=True, verbose_name="Sello de Firma", upload_to=selloPath,
        validators=[FileExtensionValidator(allowed_extensions=["png"]), FileDimensionValidator(130, 100)],
        help_text=["El tamaño debe de ser 130x100"]
    )
    sello_cargo = models.ImageField(
        null=True, blank=True, verbose_name="Sello de Cargo", upload_to=selloPath,
        validators=[FileExtensionValidator(allowed_extensions=["png"]), FileDimensionValidator(200, 70)],
        help_text=["El tamaño debe de ser 200x70"]
    )
    sello_vistobueno = models.ImageField(
        null=True, blank=True, verbose_name="Sello de VB", upload_to=selloPath,
        validators=[FileExtensionValidator(allowed_extensions=["png"]), FileDimensionValidator(200, 70)],
        help_text=["El tamaño debe de ser 200x70"]
    )
    sello_firma_adicional = models.ImageField(
        null=True, blank=True, verbose_name="Sello de Firma Adicional", upload_to=selloPath,
        validators=[FileExtensionValidator(allowed_extensions=["png"]), FileDimensionValidator(200, 70)],
        help_text=["El tamaño debe de ser 200x70"]
    )

    def __unicode__(self):
        return "%s - %s" % (
            self.codigo,
            self.nombrecorto
        )

    class Meta:
        verbose_name = 'Dependencia'
        verbose_name_plural = 'Dependencias'
        indexes = [
            models.Index(fields=["nombre"])
        ]


class AreaTipo(Auditoria):
    id = models.IntegerField(primary_key=True)
    codigo = models.CharField(max_length=2, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    paracomision = models.BooleanField(default=False)
    icono = models.CharField(max_length=50, default="")

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Tipo de Unidad Organizacional'
        verbose_name_plural = 'Tipos de Unidades Organizacionales'
        indexes = [
            models.Index(fields=["nombre"])
        ]


class Area(Auditoria):
    NIVELES = [
        (1, "Primer Nivel"),
        (2, "Segundo Nivel"),
        (3, "Tercer Nivel")
    ]

    codigo = models.CharField(max_length=5, default="")
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT)
    padre = models.ForeignKey("self", on_delete=models.PROTECT, related_name="subareas", blank=True, null=True)
    nivel = models.IntegerField(default=1, choices=NIVELES, verbose_name="Nivel Organizacional")
    orden = models.IntegerField(verbose_name="Orden")
    nombre = models.CharField(max_length=250, verbose_name="Nombre")
    nombrecorto = models.CharField(max_length=50, verbose_name="Nombre Corto")
    siglas = models.CharField(max_length=20, verbose_name="Siglas")
    mesadepartes = models.BooleanField(default=False, verbose_name="Mesa de Partes")
    areatipo = models.ForeignKey(AreaTipo, on_delete=models.PROTECT, verbose_name="Tipo de Unidad Organizacional")
    paracomisiones = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    jefeactual = models.OneToOneField(
        "PeriodoTrabajo", on_delete=models.PROTECT, null=True, blank=True, related_name="jefearea"
    )
    modificado = models.BooleanField(default=True)
    esrindente = models.BooleanField(default=False, verbose_name="Es Rindente")
    rindentepadre = models.ForeignKey(
        'self', null=True, blank=True, verbose_name="Rindente Padre", related_name="rindenteoficinas",
        on_delete=models.PROTECT
    )
    distrito = models.ForeignKey(Distrito, null=True, blank=True, on_delete=models.PROTECT, verbose_name="Ubigeo")
    direccion = models.CharField(max_length=200, null=True, blank=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=9, null=True, blank=True, verbose_name="Teléfono")
    web = models.URLField(null=True, blank=True, verbose_name="Web Site")
    documentoautorizacion = models.BinaryField(null=True, blank=True, verbose_name="Documento Autorización")
    cargooficial = models.ForeignKey(
        Cargo, null=True, blank=True, verbose_name="Cargo Oficial", on_delete=models.PROTECT
    )
    comisiondirecta = models.BooleanField(default=False)
    mensajeria = models.BooleanField(default=False, verbose_name="Mensajería")
    mensajeriahoramaxima = models.TimeField(null=True, blank=True, verbose_name="Mensajería Hora Máxima")
    mensajeriaambito = models.ForeignKey(
        "tramite.AmbitoMensajeria", null=True, blank=True, on_delete=models.PROTECT,
        verbose_name="Ambito de Mensajería"
    )
    mensajeriadistritos = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Distritos de Mensajería"
    )
    firmamargensuperior = models.IntegerField(default=0, verbose_name="Margen Superior de la Firma")

    uppers = ["nombre", "nombrecorto", "siglas"]

    objects = AMArea()
    objetos = AMAreaNormal()

    def __unicode__(self):
        return "%s" % self.nombre

    class Meta:
        verbose_name = 'Unidad Organizacional'
        verbose_name_plural = 'Unidades Organizacionales'
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["siglas"]),
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk:
            ultorden = Area.objects.filter(padre=self.padre).order_by('-orden').first()
            self.orden = (0 if not ultorden else ultorden.orden) + 1
            ultcorr = Area.objects.order_by("-codigo").first()
            self.codigo = str((0 if not ultcorr else int(ultcorr.codigo)) + 1).zfill(5)
            self.dependencia = self.padre.dependencia
        rindentepadre = None
        padre = self.padre
        while True:
            if not padre:
                break
            elif padre.esrindente:
                rindentepadre = padre
                break
            else:
                padre = padre.padre
        self.rindentepadre = rindentepadre
        self.modificado = True
        super(Area, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
        dta = []
        from apps.tramite.models import DocumentoTipo
        for dt in DocumentoTipo.objects.filter(pordefecto=True).exclude(
                pk__in=self.documentotipoarea_set.values_list("documentotipo_id")
        ).order_by("pk"):
            dta.append(
                DocumentoTipoArea(
                    documentotipo=dt,
                    area=self,
                    creador_id=1
                )
            )
        DocumentoTipoArea.objects.bulk_create(dta)

    def PadreHijas(self):
        ids = [self.pk]
        ids += self.Hijas()
        return Area.objects.filter(
            pk__in=ids
        )

    def Hijas(self):
        ids = []
        for hija in self.subareas.all():
            ids += [hija.pk]
            if hija.subareas.count() > 0:
                ids += hija.Hijas()
        return ids

    def Presidentes(self):
        return self.trabajadores.filter(cargo__paracomision=True, cargo__esprincipal=True)

    def TrabajadoresActuales(self):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        return self.trabajadores.filter(
            inicio__lte=fechaActual
        ).filter(
            Q(fin__gte=fechaActual)
            |
            Q(fin__isnull=True)
        ).order_by("inicio")

    def MensajeriaDistritos(self):
        return ", ".join(
            list(
                Distrito.objects.filter(pk__in=eval(self.mensajeriadistritos)).values_list(
                    "nombre", flat=True
                )
            )
        )

    def Encargado(self):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        return self.trabajadores.filter(
            inicio__lte=fechaActual,
            fin__gte=fechaActual,
            tipo="EN",
            activo=True,
            encargaturaplantilla__isnull=False,
            encargaturaplantillaanulacion__isnull=True
        ).order_by("inicio").first()


class PeriodoTrabajo(Auditoria):
    PERMISOTRAMITE = (
        ('O', 'OPERADOR'),
        ('T', 'TRAMITADOR DOCUMENTAL'),
    )
    TIPOS = [
        ('NN', 'Normal'),
        ('EN', 'Encargatura de Funciones'),
        ('EP', 'Encargatura de Puesto'),
        ('AP', 'Apoyo'),
    ]
    APOYOFORMAS = [
        ('A', 'Administrativo'),
        ('T', 'Técnico')
    ]
    JEFEMODOS = [
        ('NO', 'NO'),
        ('TI', 'TITULAR'),
        ('TE', 'TITULAR ENCARGADO'),
        ('TS', 'SEGUNDO TITULAR'),
        ('TT', 'TERCER TITULAR')
    ]

    area = models.ForeignKey(Area, related_name="trabajadores", on_delete=models.PROTECT)
    iniciales = models.CharField(max_length=10, null=True, blank=True)
    inicio = models.DateTimeField()
    fin = models.DateTimeField(blank=True, null=True)
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, related_name="trabajos")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, verbose_name="Cargo")
    poscargo = models.CharField(max_length=30, null=True, blank=True, verbose_name="Pos Cargo")
    permisotramite = models.CharField(max_length=1, choices=PERMISOTRAMITE, verbose_name="Modo")
    esapoyo = models.BooleanField(default=False, verbose_name="Es Apoyo")
    esjefemodo = models.CharField(max_length=2, default='NO', verbose_name="Es Jefe", choices=JEFEMODOS)
    esjefe = models.BooleanField(default=False, verbose_name="Es Jefe")
    tipo = models.CharField(max_length=2, choices=TIPOS, default="NN")
    documentosustento = models.ForeignKey("tramite.Documento", on_delete=models.PROTECT, null=True, blank=True)
    aprobador = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True, related_name='presidentesaprobados'
    )
    aprobadorfecha = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    encargaturaplantilla = models.BinaryField(blank=True, null=True, verbose_name="Sustento Encargatura")
    encargaturaplantillaanulacion = models.BinaryField(blank=True, null=True, verbose_name="Sustento Anulación")
    modificado = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    apoyoarea = models.ForeignKey(
        Area, null=True, blank=True, verbose_name="Área de Apoyo", on_delete=models.PROTECT
    )
    apoyoforma = models.CharField(max_length=1, choices=APOYOFORMAS, default="A", verbose_name="Forma de Apoyo")
    emiteexterno = models.BooleanField(default=False, verbose_name="Emite Externo")
    seguimientocompleto = models.BooleanField(default=False, verbose_name="Seguimiento Completo")
    esmensajero = models.BooleanField(default=False, verbose_name="Mensajero")

    objects = AMPeriodoTrabajo()

    # trabajadoresactuales = AMTrabajadoresActuales()

    def __unicode__(self):
        return "%s - %s" % (self.persona, self.area)

    class Meta:
        verbose_name = 'Periodo de Trabajo'
        verbose_name_plural = 'Periodos de Trabajo'
        ordering = ["persona__apellidocompleto"]

    def clean(self):
        cl = super(PeriodoTrabajo, self).clean()
        if self.inicio and self.fin:
            if self.inicio > self.fin:
                raise ValidationError("La fecha inicial no puede ser mayor a la final")
        if self.tipo == "EN":
            crucefechas = PeriodoTrabajo.objects.filter(
                area=self.area,
                tipo="EN",
            ).filter(
                Q(inicio__lte=self.inicio, fin__gte=self.inicio)
                |
                Q(inicio__lte=self.fin, fin__gte=self.fin)
            ).exclude(
                pk=self.pk
            ).exclude(
                encargaturaplantillaanulacion__isnull=False
            )
            if crucefechas.count() > 0:
                pt = crucefechas.first()
                mensaje = "Error de fechas, ya existe una encargatura de ese rango de fechas a %s en %s. " \
                          "Tiene que eliminar o anular la encargatura de rango existente."
                raise ValidationError(
                    mensaje % (
                        pt.persona.nombrecompleto,
                        pt.area.nombre
                    )
                )
        elif self.tipo == "EP":
            crucefechas = PeriodoTrabajo.objects.filter(
                area=self.area,
                tipo="EP"
            ).annotate(
                fecfin=Case(
                    When(
                        fin__isnull=True,
                        then=Value(timezone.now())
                    ),
                    default=F("fin")
                )
            ).filter(
                inicio__lte=self.inicio,
                fecfin__gte=self.inicio
            ).exclude(
                pk=self.pk
            )
            if crucefechas.count() > 0:
                pt = crucefechas.first()
                mensaje = "Error de fechas, ya existe una encargatura por puesto de ese rango de fechas a %s en %s. " \
                          "Tiene que eliminar o anular la encargatura de rango existente."
                raise ValidationError(
                    mensaje % (
                        pt.persona.nombrecompleto,
                        pt.area.nombre
                    )
                )
        elif self.esjefemodo not in ['NO']:  # and self.tipo not in ['EN', 'EP']:
            pt = TrabajadoresActuales().filter(
                area=self.area,
                esjefemodo=self.esjefemodo
            ).exclude(
                esjefemodo="NO"
            ).exclude(pk=self.pk).first()
            if pt:
                mensaje = "Dentro del área %s ya existe un %s: %s"
                raise ValidationError(
                    mensaje % (
                        pt.area.nombre,
                        pt.get_esjefemodo_display(),
                        pt.persona.nombrecompleto
                    )
                )
        return cl

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        pk = self.pk
        if not pk or not self.iniciales:
            self.iniciales = self.GenerarIniciales()
        self.esjefe = (self.esjefemodo != 'NO')
        self.modificado = True
        if self.aprobador:
            self.aprobadorfecha = timezone.now()
        if self.tipo == "AP":
            self.apoyoarea = self.persona.ultimoperiodotrabajo.area
        super(PeriodoTrabajo, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            persona = self.persona
            persona.save()
        if self.tipo == "NN" and not self.area.paracomisiones and self.esjefemodo == "TI":
            area = self.area
            # area.jefeactual = TrabajadoresActuales().filter(
            #     esjefe=True, area=self.area
            # ).first()
            area.jefeactual = self
            area.save()
        elif self.area.paracomisiones and self.cargo.esprincipal and self.activo \
                and (self.area.documentoautorizacion or self.area.comisiondirecta):
            area = self.area
            area.jefeactual = self
            area.save()

    def GenerarIniciales(self):
        _result = ""
        palabras = self.persona.nombrecompleto.split(" ")
        for palabra in palabras:
            _result += palabra[0]
        # self.area.TrabajadoresActivos
        # Validar si alguien de los trabajadores activos ya tiene esas siglas
        return _result

    def Cargo(self):
        _result = "%s %s %s"
        cargo = self.cargo
        if self.tipo in ["EN", "EP"] or self.esjefe:
            cargo = self.area.cargooficial
        _result = _result % (
            cargo.nombref if self.persona.sexo == "F" else cargo.nombrem,
            "" if self.esjefemodo == "TE" else (self.poscargo or ""),
            "(e)" if self.esjefemodo == "TE" else ""
        )
        return _result.strip().replace("  ", " ")

    def CargoCorto(self):
        _result = "%s %s %s"
        cargo = self.cargo
        if self.tipo in ["EN", "EP"] or self.esjefe:
            cargo = self.area.cargooficial
        _result = _result % (
            cargo.nombrecorto,
            "" if self.esjefemodo == "TE" else (self.poscargo or ""),
            "(e)" if self.esjefemodo == "TE" else ""
        )
        return _result.strip().replace("  ", " ")

    def CargoPeriodo(self):
        _result = "%s %s"
        cargo = self.cargo
        _result = _result % (
            cargo.nombref if self.persona.sexo == "F" else cargo.nombrem,
            self.poscargo or ""
        )
        return _result.strip().replace("  ", " ")

    def Encargaturas(self):
        # fechaActual = timezone.localdate(timezone.now())
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        return PeriodoTrabajo.objects.filter(
            persona=self.persona,
            inicio__lte=fechaActual,
            activo=True
        ).filter(
            Q(
                fin__gte=fechaActual,
                tipo="EN",
                encargaturaplantilla__isnull=False,
                encargaturaplantillaanulacion__isnull=True
            )
            |
            Q(
                Q(tipo="EP"),
                Q(
                    Q(fin__gte=fechaActual)
                    |
                    Q(fin__isnull=True)
                )
            )
        ).order_by("inicio")

    def EncargaturasOficina(self):
        return self.Encargaturas().filter(
            area=self.area
        )

    def EncargaturasNoOficina(self):
        return self.Encargaturas().exclude(
            area=self.area
        )

    def EsMensajero(self):
        _result = False
        if self.esmensajero:
            if self.area.mensajeria:
                _result = True
            elif self.area.rindentepadre:
                if self.area.rindentepadre.mensajeria:
                    _result = True
        return _result


class Proyeccion(Auditoria):
    areaorigen = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name="Unidad Organizacional de Origen")
    periodotrabajo = models.ForeignKey(
        PeriodoTrabajo, on_delete=models.PROTECT, verbose_name="Periodo de Trabajo", related_name="proyeccionareas"
    )

    def __unicode__(self):
        return "%s - %s" % (self.areaorigen, self.periodotrabajo.persona)

    class Meta:
        verbose_name = 'Proyección'
        verbose_name_plural = 'Proyecciones'
        ordering = ["areaorigen__nombre"]


class DocumentoTipoArea(Auditoria):
    documentotipo = models.ForeignKey(
        "tramite.DocumentoTipo", on_delete=models.PROTECT, verbose_name="Tipo de Documento"
    )
    area = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name="Unidad Organizacional")
    correlativo = models.IntegerField(default=0, verbose_name="Correlativo")

    def __unicode__(self):
        return "%s - %s" % (self.area.nombre, self.documentotipo.nombre)

    class Meta:
        verbose_name = 'Tipo de Documento por Unidad Organizacional'
        verbose_name_plural = 'Tipos de Documento por Unidad Organizacional'
        ordering = ["documentotipo__nombre"]


def TrabajadoresActuales():
    fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
    return PeriodoTrabajo.objects.filter(
        inicio__lte=fechaActual,
        activo=True
    ).filter(
        Q(fin__isnull=True)
        |
        Q(fin__gte=fechaActual)
    ).filter(
        Q(tipo="AP", apoyoforma="T")
        |
        Q(tipo__in=["NN", "EP"])
        |
        Q(tipo="EN", encargaturaplantilla__isnull=False, encargaturaplantillaanulacion__isnull=True)
    )
