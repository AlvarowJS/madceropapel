"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import datetime
import io
import json
import os
import uuid
from html import escape

import pyqrcodeng
from PIL import Image
from PyPDF2 import PdfFileReader
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Case, When, Value, Count, Q
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.organizacion.models import Dependencia, Area, PeriodoTrabajo, DocumentoTipoArea
from apps.inicio.models import Persona, PersonaJuridica, Distrito, Cargo
from apps.tramite.managers import AMExpediente, AMDocumento, AMDestino, AMDocumentoFirma, AMAnexoFirma, \
    AMDocumentoClean, AMDistribuidor, AMCargoExternoDetalle
from modulos.utiles.clases.formularios import Auditoria
from modulos.utiles.clases.varios import randomString, replace_characters, RemoverCaracteresEspeciales, DiasHabiles


class Expediente(Auditoria):
    anio = models.IntegerField()
    numero = models.BigIntegerField()
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT, verbose_name="expedientes")

    objects = AMExpediente()

    def __unicode__(self):
        return "%s-%s-%s" % (
            self.dependencia.codigo,
            self.anio,
            str(self.numero).zfill(settings.CONFIG_APP["ExpedienteZero"])
        )

    class Meta:
        verbose_name = 'Expediente'
        verbose_name_plural = 'Expedientes'
        unique_together = ["dependencia", "anio", "numero"]
        indexes = [
            models.Index(fields=["anio", "numero"]),
            models.Index(fields=["numero"]),
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk:
            ultexp = Expediente.objects.filter(anio=self.anio, dependencia=self.dependencia).order_by("-numero").first()
            self.numero = (0 if not ultexp else ultexp.numero) + 1
        super(Expediente, self).save(force_insert, force_update, using, update_fields)

    @property
    def qr(self):
        doc = self.documentos.order_by("pk").first()
        return doc.qr


class DocumentoTipo(Auditoria):
    id = models.IntegerField(primary_key=True)
    codigo = models.CharField(max_length=20, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    nombrecorto = models.CharField(max_length=15, verbose_name="Nombre Corto", default="")  # , unique=True)
    esmultiple = models.BooleanField(default=False, verbose_name="Es Múltiple")
    tieneforma = models.BooleanField(default=False, verbose_name="Tiene Forma")
    esmultipledestino = models.BooleanField(default=False, verbose_name="Es Múltiple Destino")
    plantillaautomatica = models.BooleanField(default=False, verbose_name="Plantilla Automática")
    usoprofesional = models.BooleanField(default=False, verbose_name="Uso Profesional")
    usoexterno = models.BooleanField(default=False, verbose_name="Uso Externo")
    firmamultiple = models.BooleanField(default=False, verbose_name="Firma Múltiple")
    paranotificacion = models.BooleanField(default=False, verbose_name="Para Notificación")
    firmaavanzada = models.BooleanField(default=False, verbose_name="Firma Avanzada")
    mesadepartesvirtual = models.BooleanField(default=False, verbose_name="Mesa de Partes Virtual")
    pordefecto = models.BooleanField(default=False, verbose_name="Por Defecto")
    autorizacomision = models.BooleanField(default=False, verbose_name="Autoriza Comisión")
    siglassinproyeccion = models.BooleanField(default=False, verbose_name="Siglas sin Proyección")
    correlativounico = models.BooleanField(default=False, verbose_name="Correlativo Único")
    paraderivacion = models.BooleanField(default=False, verbose_name="Para Derivación")

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'
        indexes = [
            models.Index(fields=["nombre"])
        ]


class DocumentoTipoPlantilla(Auditoria):
    documentotipo = models.ForeignKey(DocumentoTipo, on_delete=models.PROTECT)
    archivo = models.BinaryField()
    archivoparacontenido = models.BinaryField(null=True, blank=True, verbose_name="Archivo Para Contenido")
    archivoposfirma = models.BinaryField(null=True, blank=True, verbose_name="Archivo Pos Firma")
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT)
    referenciatabs = models.CharField(max_length=100, default="")

    def __unicode__(self):
        return self.documentotipo

    class Meta:
        verbose_name = 'Plantilla de Tipo de Documento'
        verbose_name_plural = 'PLantillas de Tipo de Documento'


class PersonalNumeracion(Auditoria):
    documentotipoarea = models.ForeignKey(
        DocumentoTipoArea, on_delete=models.PROTECT, related_name="numeracionpersonal"
    )
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, related_name="numeraciones")
    numero = models.IntegerField()

    def __unicode__(self):
        return "%s - %s" % (
            self.persona.apellidocompleto,
            self.documentotipoarea.area.nombre
        )

    class Meta:
        verbose_name = 'Numeración Personal'
        verbose_name_plural = 'Numeraciones Personales'


class Documento(Auditoria):
    PERSONAJURIDICATIPO = [
        ('R', 'RUC'),
        ('O', 'OTRO'),
    ]
    ORIGENTIPO = [
        ('O', 'EMISIÓN DE OFICINA'),
        ('P', 'EMISIÓN PROFESIONAL'),
        ('F', 'MESA DE PARTES FÍSICA'),
        ('V', 'MESA DE PARTES VIRTUAL'),
        ('I', 'INTEROPERABILIDAD'),
        ('C', 'COURRIER'),
        ('A', 'ACCESO A LA INFORMACIÓN'),
        # ('S', 'SUT') -> , TUPA (SERVICIOS)
    ]
    REMITENTETIPO = [
        ('C', 'CIUDADANO'),
        ('J', 'PERSONA JURÍDICA'),
    ]
    FORMAS = [
        ("I", "Individual"),
        ("L", "Listado"),
    ]
    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, related_name="documentos", null=True, blank=True
    )
    documentotipoarea = models.ForeignKey(DocumentoTipoArea, on_delete=models.PROTECT, verbose_name="Tipo de Documento")
    forma = models.CharField(max_length=1, default="I", choices=FORMAS, verbose_name="Forma")
    origentipo = models.CharField(max_length=1, choices=ORIGENTIPO)
    numero = models.IntegerField(verbose_name="Número", null=True, blank=True)
    anio = models.IntegerField(verbose_name="Año")
    presiglas = models.CharField(max_length=50, default="")
    siglas = models.CharField(max_length=50, null=True, blank=True)
    folios = models.IntegerField(default=0)
    asunto = models.TextField()
    fecha = models.DateField()
    diasatencion = models.IntegerField(default=0, verbose_name="Días Atención")
    responsable = models.ForeignKey(
        PeriodoTrabajo, on_delete=models.PROTECT, null=True, blank=True, related_name="documentosfirmados"
    )
    emisor = models.ForeignKey(
        PeriodoTrabajo, on_delete=models.PROTECT, null=True, blank=True, related_name="documentosemitidos"
    )
    areavirtualdestino = models.CharField(
        max_length=250, verbose_name="Unidad Organizacional Virtual Destino", null=True, blank=True
    )
    remitentetipo = models.CharField(
        max_length=1, choices=REMITENTETIPO, default='C', verbose_name="Tipo de Remitente"
    )
    personajuridicatipo = models.CharField(
        max_length=1, choices=PERSONAJURIDICATIPO, null=True, blank=True, verbose_name="Tipo Persona Jurídica"
    )
    personajuridica = models.ForeignKey(
        PersonaJuridica, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Persona Jurídica"
    )
    ciudadanoemisor = models.ForeignKey(
        Persona, on_delete=models.PROTECT, blank=True, null=True, related_name="emisorendocumento",
        verbose_name="Emisor"
    )
    ciudadanocargo = models.CharField(max_length=150, verbose_name="Cargo", default="", blank=True)
    ciudadanotramitador = models.ForeignKey(
        Persona, on_delete=models.PROTECT, blank=True, null=True, related_name="tramitadorendocumento",
        verbose_name="Ciudadano Tramitador"
    )
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, verbose_name="Teléfono", blank=True, null=True)
    distrito = models.ForeignKey(Distrito, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Distrito")
    direccion = models.CharField(max_length=250, verbose_name="Dirección", blank=True, null=True)
    direccionreferencia = models.TextField(verbose_name="Referencia", blank=True, null=True)
    observacion = models.TextField(max_length=500, verbose_name="Observación", blank=True, null=True)
    ultimoestado = models.OneToOneField(
        "DocumentoEstado", on_delete=models.PROTECT, blank=True, null=True, related_name="documentoestados"
    )
    estadoemitido = models.OneToOneField(
        "DocumentoEstado", on_delete=models.PROTECT, blank=True, null=True, related_name="documentoemitido"
    )
    clave = models.CharField(max_length=6, blank=True, null=True)
    verificado = models.BooleanField(default=False)
    notificar = models.BooleanField(default=False)
    confidencial = models.BooleanField(default=False, verbose_name="Privado")
    archivoexterno = models.URLField(null=True, blank=True, verbose_name="Archivo Externo")
    anularemision = models.BooleanField(default=False, verbose_name="Permitir Anular Emisión")

    objects = AMDocumento()
    objetos = AMDocumentoClean()

    def __unicode__(self):
        return "%s - %s" % (
            self.documentotipoarea.documentotipo.nombre,
            self.numero
        )

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, generardoc=False):
        pk = self.pk
        self.asunto = replace_characters(self.asunto)
        self.anularemision = False
        if not pk:
            # fechaActual = timezone.now()
            fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            self.anio = fechaActual.year
            self.fecha = fechaActual.date()
            self.clave = randomString(6, mayusculas=True, modo="NL")
            if self.origentipo in ["O", "P"]:
                self.presiglas = settings.CONFIG_APP["SiglasDocInicio"]
        # if self.confidencial:
        #     self.confidencialclave = randomString(5, True, "NL")
        if self.origentipo in ['O', 'P'] and generardoc:
            if not pk or not self.numero or self.responsable != Documento.objects.get(pk=self.pk).responsable:
                if self.documentotipoarea.documentotipo.correlativounico:
                    self.siglas = ""
                    ultdoc = Documento.objects.filter(
                        origentipo=self.origentipo,
                        anio=self.anio,
                        documentotipoarea__documentotipo=self.documentotipoarea.documentotipo,
                        numero__isnull=False
                    ).order_by("-numero").first()
                    self.numero = (0 if not ultdoc else ultdoc.numero) + 1
                else:
                    self.siglas, area = self.obtenerSiglas()
                    self.numero = self.obtenerNumero(area)
            if not self.expediente:
                self.expediente = Expediente.objects.create(
                    anio=self.anio,
                    dependencia=self.creador.persona.ultimoperiodotrabajo.area.dependencia,
                    creador=self.creador
                )
        if self.origentipo in ['F', 'V', 'X', 'C', 'A']:
            if not self.expediente:
                self.expediente = Expediente.objects.create(
                    anio=self.anio,
                    dependencia=self.creador.persona.ultimoperiodotrabajo.area.dependencia,
                    creador=self.creador
                )
        super(Documento, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            if self.origentipo in ["O", "P"]:
                cue = "PY"
            else:
                cue = "RE"
            DocumentoEstado.objects.create(
                documento=self,
                estado=cue,
                creador=self.creador
            )
            # Copiamos la plantilla en blanco
            plantilla = self.documentotipoarea.documentotipo.documentotipoplantilla_set.first()
            if plantilla:
                plantilla = plantilla.archivo
            DocumentoPlantilla.objects.create(
                documento=self,
                plantilla=plantilla,
                contenido=None,
                creador=self.creador
            )

    def qrtext(self):
        return "%s?%s" % (
            settings.CONFIG_APP["WebVerificador"],
            base64.b64encode(
                bytes("%s-%s-%s-%s" % (
                    self.expediente.dependencia.codigo,
                    self.expediente.anio,
                    str(self.expediente.numero),
                    self.clave
                ), "ascii")
            ).decode("ascii")
        )

    @property
    def qr(self):
        qr = pyqrcodeng.create(self.qrtext(), error="H")
        qrbytes = io.BytesIO()
        qr.png(qrbytes, scale=10, module_color=(0, 0, 0, 255))
        qrimg = Image.open(qrbytes)
        logoruta = os.path.join(settings.STATICFILES_DIRS[0], 'grc-192x192_bn.png')
        logoimg = Image.open(logoruta)
        logoancho = 100
        logoalto = 100
        box = (
            int((qrimg.width - logoancho) / 2),
            int((qrimg.height - logoalto) / 2),
            int((qrimg.width - logoancho) / 2) + logoancho,
            int((qrimg.height - logoalto) / 2) + logoalto
        )
        logoimg = logoimg.resize((logoancho, logoalto))
        qrimg.paste(logoimg, box)
        qrbytes = io.BytesIO()
        qrimg.save(qrbytes, format=qrimg.format)
        return "data:image/png;base64,%s" % base64.b64encode(qrbytes.getvalue()).decode("utf-8")

    def obtenerSiglas(self, area=None):
        _siglas = ""
        _prisep = "/"
        _areaproyeccion = None
        if area:
            arearesponsable = Area.objects.get(pk=area)
        else:
            arearesponsable = self.responsable.area
        if arearesponsable.areatipo.codigo == "FU":
            arearesponsable = arearesponsable.padre
        else:
            if self.emisor.area != arearesponsable and not self.documentotipoarea.documentotipo.siglassinproyeccion:
                _areaproyeccion = self.emisor.area
                _prisep = "-"
        if (not arearesponsable.esrindente and arearesponsable.nivel in [1, 2]) or arearesponsable.esrindente:
            _siglas = "%s%s" % (_prisep, arearesponsable.siglas)
        if arearesponsable.nivel in [3] and not arearesponsable.areatipo.codigo == "FU":
            _prisep = "-"
            _siglas = "%s%s/%s" % (
                _prisep,
                arearesponsable.padre.siglas,
                arearesponsable.siglas
            )
        if _areaproyeccion and not _areaproyeccion.areatipo.codigo == "FU":
            _siglasseg = _areaproyeccion.siglas
            _siglas = "%s-%s" % (
                _siglas,
                _siglasseg
            )
        if self.origentipo == "P":
            _siglas = _siglas.replace("/", "-")
            _siglas = "%s/%s" % (_siglas, self.responsable.iniciales)
        return _siglas, arearesponsable

    def obtenerNumero(self, area):
        area = area or self.responsable.area
        ultimodocumento = None
        if self.origentipo == "O":
            # ultimodocumento = Documento.objects.filter(
            #     numero__isnull=False,
            #     documentotipoarea__documentotipo=self.documentotipoarea.documentotipo,
            #     documentotipoarea__area=area,
            #     anio=self.anio,
            #     origentipo=self.origentipo
            # ).order_by("-numero")
            dta = self.documentotipoarea
            dta.correlativo += 1
            dta.save()
            return dta.correlativo
        elif self.origentipo == "P":
            ultimodocumento = Documento.objects.filter(
                numero__isnull=False,
                documentotipoarea__documentotipo=self.documentotipoarea.documentotipo,
                responsable__area=self.responsable.area,
                responsable__persona=self.responsable.persona,
                anio=self.anio,
                origentipo=self.origentipo
            ).order_by("-numero")
            return (ultimodocumento.first().numero if ultimodocumento else 0) + 1

    def numeroStamp(self):
        prepos = ""
        numero = self.numero or 0
        nro = " N° "
        posnum = "-"
        if self.origentipo in ["O", "P"]:
            prepos = settings.CONFIG_APP["DocumentoPreposDigital"]
        else:
            posnum = ""
        if numero == 0:
            nro = ""
            prepos = " "
            posnum = ""
        _result = "%s%s%s%s%s" % (
            self.documentotipoarea.documentotipo.nombre,
            nro,
            prepos,
            "s/n " if numero == 0 else str(numero),
            posnum
        )
        if self.origentipo in ["O", "P"]:
            _result += "%s-%s" % (self.anio, self.presiglas)
        return _result

    def obtenerNumeroSiglas(self):
        _result = self.numeroStamp()
        _format = "%s%s"
        if self.origentipo in ["O", "P"]:
            _result = _format % (_result, self.siglas or "")
        else:
            siglas = self.siglas or ""
            if siglas.startswith("-"):
                siglas = siglas[1:]
            elif len(siglas) > 0:
                siglas = "-%s" % siglas
            _result = _format % (_result, siglas)
        return _result

    def nombreDocumentoParteNumero(self):
        _result = ""
        if (self.numero or 0) > 0:
            if self.origentipo in ["F", "V", "X", "C"]:
                separador = ""
                if len(self.siglas or "") > 0 and not (self.siglas or "").startswith("-"):
                    separador = "-"
                _result = "%s%s%s" % (
                    self.numero,
                    separador,
                    self.siglas or ""
                )
            else:
                _result = "%s%s%s" % (
                    settings.CONFIG_APP["DocumentoPreposDigital"],
                    self.numero,
                    self.siglas or ""
                )
        else:
            if self.origentipo in ["F", "V", "X", "C"]:
                _result = "s/n"
        return _result

    def nombreDocumentoNumero(self):
        _result = ""
        if self.origentipo in ["F", "V"] and self.numero is not None:
            _result = self.numeroStamp()
        else:
            if self.responsable.area:
                siglas, area = self.obtenerSiglas(self.responsable.area.pk)
                _result = "%s s/n %s-%s%s" % (
                    self.documentotipoarea.documentotipo.nombre,
                    self.anio,
                    self.presiglas,
                    siglas
                )
        return _result

    def nombreDocumentoNumeroMin(self):
        if self.origentipo == "F" and self.numero is not None:
            return self.numeroStamp()
        else:
            return "%s %s%s" % (
                self.documentotipoarea.documentotipo.nombrecorto,
                settings.CONFIG_APP["DocumentoPreposDigital"],
                self.numero
            )

    def nombreDoc(self):
        _result = self.documentotipoarea.documentotipo.nombre
        if self.numero:
            if self.origentipo in ["O", "P"]:
                _result = "%s %s%s" % (
                    _result,
                    settings.CONFIG_APP["DocumentoPreposDigital"],
                    self.numero
                )
            else:
                _result = "%s %s" % (
                    _result,
                    self.numero
                )
        return _result

    def nombreDocumento(self):
        return "%s.docx" % self.nombreDoc()

    def nombreDocumentoPdf(self):
        return "%s.pdf" % self.nombreDoc()

    def AdicionalesFirmas(self):
        return self.firmas.filter(modo="FI").exclude(estado__codigo="FI").count()

    def AdicionalesVistosBuenos(self):
        return self.firmas.filter(modo="VB").exclude(estado__codigo="FI").count()

    def FirmaTitular(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(documentopdf__estado__in=["G", "V"]).count()

    def PorEmitir(self):
        return self.AdicionalesFirmas() == 0 and self.AdicionalesVistosBuenos() == 0 and self.FirmaTitular() == 0

    def ArchivosPorFirmar(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(
            documentopdf__estado__in=["G", "V"]
        ).count() > 0

    def DocumentoPorFirmar(self):
        return self.firmas.filter(estado__codigo="FI").count() == self.firmas.count()

    def DocumentoPorFirmarVBObservado(self):
        return self.firmas.filter(estado__codigo="RE").count()

    def TramiteDocumentosCargados(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(documentopdf__pdf__isnull=False).count()

    def TramiteDocumentosFaltantes(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(documentopdf__pdf__isnull=True).count()

    def Remitente(self):
        if self.origentipo in ["O", "P"]:
            dato1 = self.responsable.area.nombrecorto
            dato2 = self.responsable.persona.NombreCorto()
        else:
            if self.remitentetipo == "C":
                dato1 = self.ciudadanoemisor.NombreCorto()
                dato2 = self.ciudadanoemisor.numero
            else:
                dato1 = self.personajuridica.nombrecomercial or self.personajuridica.razonsocial
                dato2 = self.personajuridica.ruc
        _result = "<strong>%s</strong> - %s" % (
            dato1,
            dato2
        )
        return _result

    def SiglasDoc(self):
        _result = self.siglas
        if _result:
            if _result[0] in ["/", "-"]:
                _result = _result[1:]
        else:
            _result = ""
        return _result

    def EstadoIcono(self, estado, nombre, motivo=None):
        _return = "<i class='%s fa-1x mr-2' rel='tooltip' title='" + escape(nombre) + "'></i>"
        if estado == "NL":
            _return = _return % "far fa-eye-slash"
        elif estado == "LE":
            _return = _return % "far fa-eye"
        elif estado == "RE":
            _return = _return % "fas fa-hands-helping"
        elif estado == "AT":
            _return = _return % "far fa-check-circle"
        elif estado == "RH":
            _return = "<i class='%s fa-1x mr-2' data-toggle='popover' data-html='true' " \
                      "data-content='%s'></i>"
            _return = _return % ("fas fa-exclamation-triangle text-danger", escape(motivo))
        else:
            _return = ""
        return _return

    def _FListaDestinos(self, separador=', ', cantidad=0, numerar=False):
        destinos = ""
        contador = 0
        for des in self.des_documento.exclude(ultimoestado__estado="AN").order_by("pk"):
            contador += 1
            numero = ""
            if numerar and self.documentotipoarea.documentotipo.esmultiple:
                numero = "%s. " % contador
            if des.tipodestinatario == "UO":
                destinos += "%s%s<strong>%s</strong> - %s%s" % (
                    self.EstadoIcono(
                        des.ultimoestado.estado,
                        des.ultimoestado.get_estado_display(),
                        des.ultimoestado.observacion
                    ),
                    numero,
                    des.periodotrabajo.area.nombrecorto,
                    des.periodotrabajo.persona.NombreCorto(),
                    separador
                )
            elif des.tipodestinatario == "PJ":
                destinos += "%s<strong>%s</strong> %s%s" % (
                    numero,
                    des.personajuridica.ruc if des.personajuridica.tipo == "R" else "OTRO",
                    des.personajuridica.nombrecomercial or des.personajuridica.razonsocial,
                    separador
                )
            elif des.tipodestinatario == "CI":
                destinos += "%s<strong>%s</strong> %s%s" % (
                    numero,
                    des.persona.numero,
                    des.persona.apellidocompleto,
                    separador
                )
            elif des.tipodestinatario == "DP":
                destinos += "%s<strong>%s</strong> %s%s" % (
                    numero,
                    des.dependencia_responsable.numero,
                    des.dependencia_responsable.apellidocompleto,
                    separador
                )
        if cantidad > 0:
            destinos = destinos[:-cantidad]
        return destinos

    def ListaDestinos(self):
        return self._FListaDestinos(cantidad=2)

    def ListaDestinosBandeja(self):
        return self._FListaDestinos(separador="<br/>", numerar=True)

    def estadoFirmas(self):
        _result = ""
        if self.ultimoestado.estado == "OF" and self.ultimoestado.observacion:
            _result += '<span class="label label-pill label-inline my-1 label-light-danger" ' \
                       'rel="tooltip" title="%s">DOC OBSERVADO</span>' % (
                           self.ultimoestado.observacion
                       )
        elif self.firmas.filter(estado__codigo='RE').count() > 0:
            _result += '<span class="label label-pill label-inline my-1 label-light-danger">OBSERVADO : %s</span>' % \
                       self.firmas.filter(estado__codigo='RE').count()
        elif self.AdicionalesFirmas() + self.AdicionalesVistosBuenos() > 0:
            if self.AdicionalesFirmas() > 0:
                _result += '<div>Firma Ad Pendiente: <span class="font-weight-bolder">%s</span></div>' % \
                           self.AdicionalesFirmas()
            if self.AdicionalesVistosBuenos() > 0:
                _result += '<div class="mt-1">V°B° Pendiente: <span class="font-weight-bolder">%s</span></div>' % \
                           self.AdicionalesVistosBuenos()
        elif self.FirmaTitular() > 0:
            _result += '<span class="my-1">Firma Titular Pendiente</span>'
        elif self.PorEmitir() > 0:
            _result += '<span class="my-1">Emisión Pendiente</span>'
        return _result

    def DestinosTablero(self):
        _result = ""
        for destino in self.des_documento.exclude(ultimoestado__estado="AN").order_by("pk")[:2]:
            _result += destino.obtenerNombreDestino() + ", "
        _result = _result[:-2]
        if self.des_documento.exclude(ultimoestado__estado="AN").count() > 2:
            _result += " y más..."
        return _result

    def DestinosTableroPersona(self):
        _result = ""
        for destino in self.des_documento.exclude(ultimoestado__estado="AN").order_by("pk")[:2]:
            _result += destino.obtenerNombreDestinoPersona() + ", "
        _result = _result[:-2]
        if self.des_documento.exclude(ultimoestado__estado="AN").count() > 2:
            _result += " y más..."
        return _result

    def ReferenciaRespuesta(self):
        return self.referencias.filter(destino__isnull=False).first()

    def ListaDestinosPdf(self):
        _result = None
        if self.documentotipoarea.documentotipo.esmultiple and \
                not self.documentotipoarea.documentotipo.esmultipledestino and \
                self.forma == "I":
            _result = json.dumps(list(
                self.documentoplantilla.documentopdf_set.annotate(
                    desnombreofi=Case(
                        When(destino__tipodestinatario="UO", then=F("destino__periodotrabajo__area__nombre")),
                        When(
                            destino__tipodestinatario="PJ",
                            then=Case(
                                When(
                                    destino__personajuridica__nombrecomercial__isnull=True,
                                    then=F("destino__personajuridica__razonsocial")
                                ),
                                default=F("destino__personajuridica__nombrecomercial")
                            )
                        ),
                        When(destino__tipodestinatario="CI", then=F("destino__persona__apellidocompleto")),
                        When(destino__tipodestinatario="DP",
                             then=F("destino__dependencia_responsable__apellidocompleto")),
                        default=Value("")
                    ),
                    desnombreper=Case(
                        When(
                            destino__tipodestinatario="UO",
                            then=F("destino__periodotrabajo__persona__apellidocompleto")
                        ),
                        When(
                            destino__tipodestinatario="PJ", then=Case(
                                When(destino__persona__isnull=False, then=F("destino__persona__apellidocompleto")),
                                default=Value("PERSONA JURIDICA")
                            )
                        ),
                        When(destino__tipodestinatario="CI", then=Value("CIUDADANO")),
                        When(
                            destino__tipodestinatario="DP",
                            then=F("destino__dependencia_responsable__apellidocompleto")
                        ),
                        default=Value("")
                    ),
                    descodigo=F("destino__pk"),
                    descodigopadre=F("destino__documento__pk"),
                    desforma=F("destino__tipotramite__nombre"),
                    desformacodigo=F("destino__tipotramite__codigo")
                ).order_by("pk").values(
                    "desnombreofi", "desnombreper", "descodigo", "descodigopadre",
                    "desforma", "desformacodigo"
                )
            ))
        return _result

    def tienePdfs(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(documentopdf__pdf__isnull=False).count() > 0

    def AnexosNoFirmados(self):
        return self.anexos.aggregate(
            sinfirmar=Count("firmadores", filter=Q(firmadores__estado__in=["SF", "RE"]))
        )["sinfirmar"]

    def DestinosExternos(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(tipodestinatario__in=["PJ", "CI"]).count()

    def DestinosExternosMensajeria(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").filter(
            tipodestinatario__in=["PJ", "CI"],
            mensajeriamodoentrega__codigo__in=["MG"]
        ).count()

    def DestinosInternos(self):
        return self.des_documento.exclude(ultimoestado__estado="AN").exclude(tipodestinatario__in=["PJ", "CI"]).count()

    def Rechazados(self):
        _result = None
        if self.des_documento.filter(ultimoestado__estado="RH").count() > 0:
            _result = []
            for destino in self.des_documento.filter(ultimoestado__estado="RH"):
                _result.append({
                    "persona": destino.ultimoestado.creador.persona.apellidocompleto,
                    "fecha": destino.ultimoestado.creado.astimezone(tz=pytz_timezone(settings.TIME_ZONE)).strftime(
                        "%d/%m/%Y %I:%M %p"
                    ),
                    "observacion": destino.ultimoestado.observacion
                })
            _result = json.dumps(_result)
        return _result

    def AnularEmision(self):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        if self.RechazadoTotal():
            if self.estadoemitido:
                fechaActual = self.estadoemitido.creado - timezone.timedelta(days=2)
        elif self.estadoemitido and (self.DestinosExternos() == 0 or settings.CONFIG_APP.get("EnDesarrollo")):
            fechaActual = self.estadoemitido.creado - timezone.timedelta(days=2)
        else:
            # Hasta 3 Días hábiles permitidos
            fechaActual -= timezone.timedelta(days=DiasHabiles(fechaActual, 3, -1))
        if self.estadoemitido:
            if self.anularemision:
                return True
            else:
                return self.ultimoestado.estado == "EM" and self.periodotrabajo_set.count() == 0 and \
                       self.estadoemitido.creado >= fechaActual
        else:
            return self.ultimoestado.estado == "EM" and self.periodotrabajo_set.count() == 0

    def FechaEmision(self):
        _result = None
        if self.estadoemitido:
            _result = self.estadoemitido.creado
        return _result

    def SegEmisorTipo(self):
        _result = ""
        if self.origentipo not in ["O", "P"]:
            if self.remitentetipo == "C":
                _result = "Ciudadano"
            elif self.remitentetipo == "J":
                _result = "Proveedor"
        return _result

    def SegEmisorNombre(self):
        _result = ""
        if self.origentipo in ["O", "P"]:
            _result = "%s - %s" % (self.responsable.area.nombre, self.responsable.persona.apellidocompleto)
        else:
            if self.remitentetipo == "C":
                # print(self.pk)
                _result = "%s" % self.ciudadanoemisor.apellidocompleto
            elif self.remitentetipo == "J":
                _result = "%s" % (self.personajuridica.nombrecomercial or self.personajuridica.razonsocial)
        return _result

    def SegEmisorDocumento(self):
        _result = ""
        if self.origentipo in ["O", "P"]:
            _result = "%s" % self.responsable.persona.apellidocompleto
        else:
            if self.remitentetipo == "C":
                if self.ciudadanoemisor.tipodocumentoidentidad.codigo in ["DNI", "CET", "PAS"]:
                    _result = "%s: %s" % (
                        self.ciudadanoemisor.tipodocumentoidentidad.codigo,
                        self.ciudadanoemisor.numero
                    )
            elif self.remitentetipo == "J" and self.personajuridica.tipo == "R":
                _result = "RUC: %s" % self.personajuridica.ruc
        return _result

    def RechazadoTotal(self):
        _canRH = self.des_documento.exclude(ultimoestado__estado="AN").filter(ultimoestado__estado="RH").count()
        _canDES = self.des_documento.exclude(ultimoestado__estado="AN").count()
        return _canRH == _canDES

    def SeHaEmitido(self):
        return self.documentoestado_set.filter(estado="EM").count() > 0

    def MensajeriaObservacion(self):
        return DestinoEstadoMensajeria.objects.filter(
            destino__documento=self,
            estado__in=["DM"]
        ).first()

    @property
    def asuntocorto(self):
        _result = self.asunto
        _maxcar = 100
        if len(_result) > _maxcar:
            _palabras = _result.split(" ")
            _result = ""
            for _palabra in _palabras:
                if len(_result + " " + _palabra) > _maxcar:
                    _result += "..."
                    break
                _result += (" " if len(_result) > 0 else "") + _palabra
        return _result

    def ConfidencialDnis(self, terminaen=None):
        _dnis = [self.responsable.persona.numero]
        if self.responsable != self.emisor:
            _dnis.append(self.emisor.persona.numero)
        for destino in self.des_documento.filter(tipodestinatario__in=["UO"]):
            if not destino.periodotrabajo.persona.numero in _dnis:
                _dnis.append(destino.periodotrabajo.persona.numero)
        if terminaen:
            __dnis = _dnis
            _dnis = []
            for dni in __dnis:
                if dni.endswith(terminaen):
                    _dnis.append(dni)
        return _dnis


class DocumentoEstado(Auditoria):
    ESTADO = [
        ('RE', 'Registrado'),
        ('EM', 'Emitido'),
        ('AN', 'Anulado'),
        ('RC', 'Rechazado'),
        ('TR', 'Transferido'),
        ('PY', 'En Proyecto'),
        ('PD', 'Despacho'),
        ('OF', 'Observación de Firma o VB'),
        ('RP', 'Recibido Parcial'),
        ('RT', 'Recibido'),
        ('AT', 'Atendido'),
        ('AR', 'Archivado')
    ]
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT)
    estado = models.CharField(max_length=2, choices=ESTADO)
    observacion = models.TextField(null=True, blank=True, verbose_name="Observación")
    firmado = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s - %s" % (
            self.documento,
            self.estado
        )

    class Meta:
        verbose_name = 'Estado del Documento'
        verbose_name_plural = 'Estados del Documento'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        pk = self.pk
        super(DocumentoEstado, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            doc = self.documento
            doc.ultimoestado = self
            if self.estado == "EM":
                doc.estadoemitido = self
            elif self.estado in ["RE", "AN", "PY", "PD"]:
                doc.estadoemitido = None
            doc.save()


class DocumentoPlantilla(Auditoria):
    documento = models.OneToOneField(Documento, on_delete=models.PROTECT)
    plantilla = models.BinaryField(null=True, blank=True)
    contenido = models.BinaryField(null=True, blank=True)
    plantillacontenido = models.BinaryField(null=True, blank=True)
    codigo = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        return self.documento

    class Meta:
        verbose_name = 'Plantilla del Documento'
        verbose_name_plural = 'Plantillas de los Documentos'
        indexes = [
            models.Index(fields=["codigo"])
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, genuuid=False):
        if genuuid:
            self.codigo = uuid.uuid4().hex
        super(DocumentoPlantilla, self).save(force_insert, force_update, using, update_fields)


class DocumentoPDF(Auditoria):
    ESTADO = [
        ('G', 'Generado'),
        ('F', 'Firmado'),
        ('O', 'Otro'),
        ('T', 'Tramitado'),
    ]
    documentoplantilla = models.ForeignKey(
        DocumentoPlantilla, on_delete=models.PROTECT, verbose_name="Plantilla del Documento"
    )
    destino = models.OneToOneField("Destino", on_delete=models.PROTECT)
    pdf = models.BinaryField(verbose_name="Archivo PDF", null=True, blank=True)
    pdffirma = models.BinaryField(verbose_name="Archivo PDF firmado", null=True, blank=True)
    estado = models.CharField(max_length=1, choices=ESTADO, default="G")

    def __unicode__(self):
        return self.documentoplantilla.documento.nombreDocumento()

    class Meta:
        verbose_name = 'Documento PDF'
        verbose_name_plural = 'Documentos PDF'

    def CrearRevision(self, request, impreso=False):
        if not request.user.is_staff:
            DocumentoPDFRevisiones.objects.create(
                documentopdf=self,
                direccionip=request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR")),
                nombreequipo=request.user_agent.get_device(),
                es_mobile=request.user_agent.is_mobile,
                es_tablet=request.user_agent.is_tablet,
                es_touch=request.user_agent.is_touch_capable,
                es_pc=request.user_agent.is_pc,
                es_bot=request.user_agent.is_bot,
                navegador_familia=request.user_agent.browser.family,
                navegador_version=request.user_agent.browser.version_string,
                so_familia=request.user_agent.os.family,
                so_version=request.user_agent.os.version_string,
                device_familia=request.user_agent.device.family,
                impreso=impreso,
                creador=request.user
            )

    def CreateToken(self, request, persona):
        dtl = None
        periodoactual = persona.periodotrabajoactual()
        if periodoactual:
            dtl = DocumentoPDFTokenLectura.objects.create(
                documentopdf=self,
                direccionip=request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR")),
                nombreequipo=request.user_agent.get_device(),
                es_mobile=request.user_agent.is_mobile,
                es_tablet=request.user_agent.is_tablet,
                es_touch=request.user_agent.is_touch_capable,
                es_pc=request.user_agent.is_pc,
                es_bot=request.user_agent.is_bot,
                navegador_familia=request.user_agent.browser.family,
                navegador_version=request.user_agent.browser.version_string,
                so_familia=request.user_agent.os.family,
                so_version=request.user_agent.os.version_string,
                device_familia=request.user_agent.device.family,
                creador=request.user,
                token=randomString(modo="L"),
                tokensolicitante=periodoactual,
                tokencorreo=persona.personaconfiguracion.correoinstitucional
            )
            dtl.tokenvalido = dtl.tokenvalido + timezone.timedelta(minutes=5)
            dtl.save()
        return dtl

    def nombreDoc(self, idx=0):
        fileNAME = self.destino.documento.nombreDoc()
        tipodest = self.destino.tipodestinatario
        if tipodest == "UO":
            fileNAME = "%s_%s_%s" % (
                fileNAME,
                self.destino.periodotrabajo.area.siglas,
                self.destino.periodotrabajo.persona.alias
            )
        elif tipodest == "PJ":
            fileNAME = "%s_%s" % (
                fileNAME,
                self.destino.personajuridica.ruc if self.destino.personajuridica.tipo == "R" else
                "OTRO"
            )
            if self.destino.persona:
                fileNAME = "%s_%s_%s" % (
                    fileNAME,
                    "" if self.destino.persona.tipodocumentoidentidad.codigo == "OTR" else
                    self.destino.persona.numero,
                    self.destino.persona.alias
                )
        elif tipodest == "CI":
            fileNAME = "%s_%s_%s" % (
                fileNAME,
                "" if self.destino.persona.tipodocumentoidentidad.codigo == "OTR" else
                self.destino.persona.numero,
                self.destino.persona.alias
            )
        elif tipodest == "DP":
            fileNAME = "%s_%s" % (
                fileNAME,
                idx
            )
        return fileNAME


class DocumentoPDFRevisiones(Auditoria):
    documentopdf = models.ForeignKey(
        DocumentoPDF, on_delete=models.PROTECT, verbose_name="Documento PDF", related_name="revisiones"
    )
    direccionip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    nombreequipo = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nombre de Equipo")
    es_mobile = models.BooleanField(default=False, verbose_name="Es Mobile")
    es_tablet = models.BooleanField(default=False, verbose_name="Es Tablet")
    es_touch = models.BooleanField(default=False, verbose_name="Es Touch")
    es_pc = models.BooleanField(default=False, verbose_name="Es PC")
    es_bot = models.BooleanField(default=False, verbose_name="Es BOT")
    navegador_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="Navegador Familia")
    navegador_version = models.CharField(max_length=200, null=True, blank=True, verbose_name="Navegador Versión")
    so_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="S.O. Familia")
    so_version = models.CharField(max_length=200, null=True, blank=True, verbose_name="S.O. Versión")
    device_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="Device Familia")
    impreso = models.BooleanField(default=False, verbose_name="Se ha impreso")

    def __unicode__(self):
        return self.nombreequipo or ""

    class Meta:
        verbose_name = 'Revisión'
        verbose_name_plural = 'Revisiones'


class DocumentoPDFTokenLectura(Auditoria):
    documentopdf = models.ForeignKey(
        DocumentoPDF, on_delete=models.PROTECT, verbose_name="Documento PDF", related_name="tokens"
    )
    direccionip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    nombreequipo = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nombre de Equipo")
    es_mobile = models.BooleanField(default=False, verbose_name="Es Mobile")
    es_tablet = models.BooleanField(default=False, verbose_name="Es Tablet")
    es_touch = models.BooleanField(default=False, verbose_name="Es Touch")
    es_pc = models.BooleanField(default=False, verbose_name="Es PC")
    es_bot = models.BooleanField(default=False, verbose_name="Es BOT")
    navegador_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="Navegador Familia")
    navegador_version = models.CharField(max_length=200, null=True, blank=True, verbose_name="Navegador Versión")
    so_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="S.O. Familia")
    so_version = models.CharField(max_length=200, null=True, blank=True, verbose_name="S.O. Versión")
    device_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="Device Familia")
    token = models.CharField(max_length=5, verbose_name="Token Código")
    tokensolicitante = models.ForeignKey(PeriodoTrabajo, on_delete=models.PROTECT, verbose_name="Solicitante")
    tokencorreo = models.EmailField(verbose_name="Token Correo")
    tokenvalido = models.DateTimeField(auto_now_add=True, verbose_name="Token Válidación Usar")
    tokencorreoenvio = models.DateTimeField(null=True, blank=True, verbose_name="Token Envío")
    tokenusado = models.DateTimeField(null=True, blank=True, verbose_name="Token Uso")

    ###
    ### token = Se genera una clave de 5 números
    ### tokensolicitante = Se guarda el periodo de trabajo del usuario logueado
    ### tokencorreo = Se guarda el correo del usuario logueado
    ### tokenvalido = Se guarda fecha actual + 1 minuto de duración del Token
    ### tokencorreoenvio = Se guarda la fecha actual en la que se envía el correo
    ### tokenusado = Se guarda la fecha actual en la que se usa el Token
    ###

    def __unicode__(self):
        return self.nombreequipo or ""

    class Meta:
        verbose_name = 'Lectura de Token'
        verbose_name_plural = 'Lecturas de Token'


class DocumentoReferenciaOrigen(Auditoria):
    orden = models.IntegerField(default=0)
    codigo = models.CharField(max_length=3)
    nombre = models.CharField(max_length=100)
    siglas = models.CharField(max_length=20, default="")
    pideanio = models.BooleanField(default=False)
    pidedependencia = models.BooleanField(default=False)
    anioinicio = models.IntegerField(default=2010)
    consultaurl = models.CharField(max_length=200, default="")
    consultausuario = models.CharField(max_length=50, default="")
    consultaclave = models.CharField(max_length=50, default="")
    tienepdf = models.BooleanField(default=False)
    tienemodos = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)

    def __unicode__(self):
        return self.siglas

    class Meta:
        verbose_name = 'Origen de Documento de Referencia'
        verbose_name_plural = 'Orígenes de Documento de Referencia'


class DocumentoReferenciaModo(Auditoria):
    orden = models.IntegerField(default=0)
    codigo = models.CharField(max_length=3)
    nombre = models.CharField(max_length=100)
    pideoficina = models.BooleanField(default=False)
    pidetipo = models.BooleanField(default=False)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Modo de Documento de Referencia'
        verbose_name_plural = 'Modos de Documento de Referencia'


class DocumentoReferencia(Auditoria):
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT, related_name="referencias")
    origen = models.ForeignKey(DocumentoReferenciaOrigen, on_delete=models.PROTECT)
    modo = models.ForeignKey(DocumentoReferenciaModo, null=True, blank=True, on_delete=models.PROTECT)
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT, null=True, blank=True)
    oficina = models.CharField(max_length=5, null=True, blank=True, verbose_name="Oficina")
    oficinanombre = models.CharField(max_length=250, null=True, blank=True, verbose_name="Oficina")
    documentotipo = models.CharField(max_length=3, null=True, blank=True, verbose_name="Tipo de Documento")
    documentotiponombre = models.CharField(max_length=250, null=True, blank=True, verbose_name="Tipo de Documento")
    anio = models.IntegerField(null=True, blank=True, verbose_name="Año")
    numero = models.IntegerField(null=True, blank=True, verbose_name="Número")
    expedientenro = models.CharField(max_length=100, verbose_name="Número de Expediente")
    expedienteemi = models.CharField(max_length=100, verbose_name="Número de Emisión", default="")
    descripcion = models.CharField(max_length=250, null=True, blank=True, verbose_name="Descripción")
    destino = models.ForeignKey(
        "Destino", on_delete=models.PROTECT, null=True, blank=True, related_name="destinoreferencias"
    )

    def __unicode__(self):
        return self.descripcion

    class Meta:
        verbose_name = 'Expediente'
        verbose_name_plural = 'Expedientes'

    def Expediente(self):
        _result = ""
        if self.origen.codigo == "SGD":
            _result = "%s-%s" % (
                self.anio,
                str(self.numero).zfill(7)
            )
        elif self.origen.codigo == "MAD":
            _result = "%s" % str(self.numero).zfill(8)
        else:
            _result = "%s-%s-%s" % (
                self.dependencia.codigo,
                self.anio,
                str(self.numero).zfill(settings.CONFIG_APP["ExpedienteZero"])
            )
        return _result


class DocumentoFirmaEstado(Auditoria):
    codigo = models.CharField(max_length=2)
    nombre = models.CharField(max_length=20)
    icono = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="")

    def __unicode__(self):
        return "%s" % self.nombre

    class Meta:
        verbose_name = 'Estado de Firma del Documento'
        verbose_name_plural = 'Estados de Firmas del Documento'


class DocumentoFirma(Auditoria):
    MODO = [
        ('FI', 'Firma Adicional'),
        ('VB', 'Visto Bueno'),
    ]
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT, related_name="firmas")
    empleado = models.ForeignKey(PeriodoTrabajo, on_delete=models.PROTECT)
    modo = models.CharField(max_length=2, choices=MODO)
    motivorechazado = models.CharField(max_length=250, blank=True, null=True)
    estado = models.ForeignKey(DocumentoFirmaEstado, on_delete=models.PROTECT)
    codigouuid = models.CharField(max_length=50, null=True, blank=True)

    objects = AMDocumentoFirma()

    def __unicode__(self):
        return "%s - %s" % (
            self.modo,
            self.estado
        )

    class Meta:
        verbose_name = 'Firma del Documento'
        verbose_name_plural = 'Firmas del Documento'
        indexes = [
            models.Index(fields=["codigouuid"])
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, genuuid=False):
        if genuuid:
            self.codigouuid = uuid.uuid4().hex
        super(DocumentoFirma, self).save(force_insert, force_update, using, update_fields)


class Anexo(Auditoria):
    descripcion = models.CharField(max_length=250)
    archivonombre = models.CharField(max_length=250)
    archivo = models.BinaryField()
    archivofirmado = models.BinaryField(blank=True, null=True)
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT, related_name="anexos")
    provienede = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT, verbose_name="anexosnuevos"
    )

    def __unicode__(self):
        return self.descripcion

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'

    def Tamanio(self):
        return len(self.archivofirmado or self.archivo)

    def Descripcion(self):
        return self.descripcion or self.archivonombre

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.descripcion = RemoverCaracteresEspeciales(self.descripcion)
        super(Anexo, self).save()

    def CrearRevision(self, request):
        if not request.user.is_staff or settings.CONFIG_APP.get("EnDesarrollo"):
            AnexoRevisiones.objects.create(
                anexo=self,
                direccionip=request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR")),
                nombreequipo=request.user_agent.get_device(),
                es_mobile=request.user_agent.is_mobile,
                es_tablet=request.user_agent.is_tablet,
                es_touch=request.user_agent.is_touch_capable,
                es_pc=request.user_agent.is_pc,
                es_bot=request.user_agent.is_bot,
                navegador_familia=request.user_agent.browser.family,
                navegador_version=request.user_agent.browser.version_string,
                so_familia=request.user_agent.os.family,
                so_version=request.user_agent.os.version_string,
                device_familia=request.user_agent.device.family,
                creador=request.user
            )

    def TieneFirmas(self):
        return self.firmadores.filter(estado="FI").count()


class AnexoRevisiones(Auditoria):
    anexo = models.ForeignKey(Anexo, on_delete=models.PROTECT, verbose_name="Anexo", related_name="revisiones")
    direccionip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    nombreequipo = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nombre de Equipo")
    es_mobile = models.BooleanField(default=False, verbose_name="Es Mobile")
    es_tablet = models.BooleanField(default=False, verbose_name="Es Tablet")
    es_touch = models.BooleanField(default=False, verbose_name="Es Touch")
    es_pc = models.BooleanField(default=False, verbose_name="Es PC")
    es_bot = models.BooleanField(default=False, verbose_name="Es BOT")
    navegador_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="Navegador Familia")
    navegador_version = models.CharField(max_length=200, null=True, blank=True, verbose_name="Navegador Versión")
    so_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="S.O. Familia")
    so_version = models.CharField(max_length=200, null=True, blank=True, verbose_name="S.O. Versión")
    device_familia = models.CharField(max_length=200, null=True, blank=True, verbose_name="Device Familia")

    def __unicode__(self):
        return self.nombreequipo or ""

    class Meta:
        verbose_name = 'Revisión de Anexo'
        verbose_name_plural = 'Revisiones de Anexo'


class AnexoFirma(Auditoria):
    MODO = [
        ('FI', 'Firma'),
        ('VB', 'Visto Bueno'),
    ]
    ESTADO = [
        ('SF', 'Sin Firma'),
        ('FI', 'Firmado'),
        ('RE', 'Rechazado'),
    ]
    anexo = models.ForeignKey(Anexo, on_delete=models.PROTECT, related_name="firmadores")
    empleado = models.ForeignKey(PeriodoTrabajo, on_delete=models.PROTECT)
    modo = models.CharField(max_length=2, choices=MODO, default="VB")
    estado = models.CharField(max_length=2, choices=ESTADO, default="SF")
    estadofecha = models.DateTimeField(blank=True, null=True)
    estadomotivo = models.CharField(max_length=250, blank=True, null=True)
    codigouuid = models.CharField(max_length=100, default="")

    objects = AMAnexoFirma()

    def __unicode__(self):
        return "%s - %s" % (
            self.modo,
            self.estado
        )

    class Meta:
        verbose_name = 'Firma del Anexo'
        verbose_name_plural = 'Firma del Anexos'
        indexes = [
            models.Index(fields=["codigouuid"])
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, genuuid=False):
        if genuuid:
            self.codigouuid = uuid.uuid4().hex
        super(AnexoFirma, self).save(force_insert, force_update, using, update_fields)


class TipoTramite(Auditoria):
    DUENIOS = [
        ("O", "Para Oficina"),
        ("T", "Para Trámite Documentario"),
    ]

    id = models.IntegerField(primary_key=True)
    codigo = models.CharField(max_length=1)
    nombre = models.CharField(max_length=250)
    estado = models.BooleanField(default=True)
    duenio = models.CharField(max_length=1, default="T", choices=DUENIOS)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Tipo de Trámite'
        verbose_name_plural = 'Tipos de Trámite'


class TipoProveido(Auditoria):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    estado = models.BooleanField(default=True)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Tipo de Proveído'
        verbose_name_plural = 'Tipos de Proveído'


class MensajeriaModoEntrega(Auditoria):
    codigo = models.CharField(max_length=2, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    icono = models.CharField(max_length=100, verbose_name="Icono")
    color = models.CharField(max_length=30, verbose_name="Color")
    estado = models.BooleanField(default=False, verbose_name="Estado")
    orden = models.IntegerField(default=100, verbose_name="Orden")
    mensajeriaestado = models.CharField(max_length=2, default="PE")

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Modo de Entrega'
        verbose_name_plural = 'Modos de Entrega'


class Destino(Auditoria):
    TIPODESTINATARIO = (
        ('UO', 'Unidad Organizacional'),
        # ('DP', 'Dependencia'),
        ('PJ', 'Persona Jurídica'),
        ('CI', 'Ciudadano'),
    )
    DISTRIBUCION = [
        ('D', 'Digital'),
        ('M', 'Digital y Físico'),
    ]
    MESAPARTESMODOENVIO = [
        (0, 'Ninguno'),
        (1, 'Imprimir los documentos y/o anexos; y entregarlos a Mensajería.'),
        # ('2', 'Que Mesa de Partes los imprima y remita. (Máximo 10 folios).')
    ]
    documento = models.ForeignKey("Documento", on_delete=models.PROTECT, related_name="des_documento")
    tipodestinatario = models.CharField(max_length=2, choices=TIPODESTINATARIO)
    diasatencion = models.IntegerField(default=0, verbose_name="Días de Atención")
    entregafisica = models.TextField(
        null=True, blank=True,
        verbose_name="ENTREGA FÍSICA (Ejemplo: 01 Expediente, 03 CDs, 01 Expediente con 180 Folios, 01 Laptop, etc.)"
    )
    entregafisicareceptor = models.ForeignKey(
        PeriodoTrabajo, null=True, blank=True, verbose_name="Recepcionador", on_delete=models.PROTECT,
        related_name="cargosfisicos"
    )
    entregafisicafecha = models.DateTimeField(null=True, blank=True, verbose_name="Recepción Fecha")
    entregafisicacargo = models.BinaryField(null=True, blank=True, verbose_name="Cargo Firmado")
    entregaimagen = models.BinaryField(blank=True, null=True, verbose_name="Foto de Recepción")
    entregauid = models.CharField(max_length=50, null=True, blank=True, verbose_name="UID de Recepción")
    entregauiduser = models.ForeignKey(User, null=True, blank=True, verbose_name="UID User", on_delete=models.PROTECT)
    periodotrabajo = models.ForeignKey(
        PeriodoTrabajo, on_delete=models.PROTECT, verbose_name="Personal", null=True, blank=True
    )
    personajuridica = models.ForeignKey(
        PersonaJuridica, on_delete=models.PROTECT, verbose_name="Entidad Externa",
        null=True, blank=True
    )
    persona = models.ForeignKey(
        Persona, on_delete=models.PROTECT, related_name="des_persona", null=True, blank=True
    )
    dependencia = models.ForeignKey(
        Dependencia, on_delete=models.PROTECT, related_name="des_dependencia", null=True, blank=True
    )
    dependencia_area = models.CharField(max_length=5, null=True, blank=True, verbose_name="Unidad Organizacional")
    dependencia_area_nombre = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Unidad Organizacional Nombre"
    )
    dependencia_responsable = models.ForeignKey(
        Persona, null=True, blank=True, verbose_name="Responsable", related_name="res_persona",
        on_delete=models.PROTECT
    )
    dependencia_responsable_cargo = models.ForeignKey(
        Cargo, null=True, blank=True, verbose_name="Responsable Cargo", related_name="car_responsable",
        on_delete=models.PROTECT
    )
    personacargo = models.CharField(max_length=200, null=True, blank=True, verbose_name="Cargo")
    ultimoestado = models.OneToOneField(
        "DestinoEstado", on_delete=models.PROTECT, related_name="des_ultimoestado", null=True, blank=True
    )
    tipotramite = models.ForeignKey(TipoTramite, on_delete=models.PROTECT, verbose_name="Trámite")
    proveido = models.ForeignKey(TipoProveido, on_delete=models.PROTECT, verbose_name="Proveído")
    indicacion = models.TextField(max_length=600, verbose_name="Indicación", null=True, blank=True)
    ubigeo = models.ForeignKey(Distrito, on_delete=models.PROTECT, related_name="des_ubigeo", null=True, blank=True)
    direccion = models.CharField(max_length=250, verbose_name="Dirección", null=True, blank=True)
    referencia = models.CharField(max_length=250, blank=True, null=True, verbose_name="Referencia de la Dirección")
    correo = models.EmailField(blank=True, null=True)
    recepcionador = models.ForeignKey(
        PeriodoTrabajo, on_delete=models.PROTECT, related_name="des_recepcionador", null=True, blank=True
    )
    recepcionfecha = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Recepción")
    distribucion = models.CharField(max_length=1, choices=DISTRIBUCION, default="D")
    distribuciondetalle = models.CharField(
        max_length=250, verbose_name="Detalle de Distribución", null=True, blank=True
    )
    distribucioncargo = models.BinaryField(blank=True, null=True, verbose_name="Archivo Cargo de Distribución")
    distribucioninicio = models.DateTimeField(blank=True, null=True, verbose_name="Inicio de Distribución del Físico")
    mesapartesmodoenvio = models.IntegerField(
        default=0, choices=MESAPARTESMODOENVIO, verbose_name="Modo de Envío a Mesa de Partes"
    )
    mensajeriamodoentrega = models.ForeignKey(
        MensajeriaModoEntrega, verbose_name="Modo de Entrega", on_delete=models.PROTECT
    )
    ultimoestadomensajeria = models.OneToOneField(
        "DestinoEstadoMensajeria", on_delete=models.PROTECT, null=True, blank=True,
        related_name="detinomensajeria"
    )
    detallemensajeria = models.OneToOneField(
        "CargoExternoDetalle", on_delete=models.PROTECT, null=True, blank=True, related_name="destinomensajeria"
    )
    documentacionfisica = models.TextField(verbose_name="Documentación Física", null=True, blank=True)

    objects = AMDestino()

    def __unicode__(self):
        return self.get_tipodestinatario_display()

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        pk = self.pk
        if not self.pk and not self.mensajeriamodoentrega:
            self.mensajeriamodoentrega = MensajeriaModoEntrega.objects.filter(estado=True).order_by("orden").first()
        super(Destino, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            estado = "RG"
            if self.documento.ultimoestado in ["EM", "RP", "RT", "AT", "AR"]:
                estado = "NL"
            DestinoEstado.objects.create(
                destino=self,
                creador=self.creador,
                estado=estado
            )

    def Folios(self):
        _result = 0
        docpdf = None
        if self.documento.documentotipoarea.documentotipo.esmultiple and \
                not self.documento.documentotipoarea.documentotipo.esmultipledestino and \
                self.documento.forma == "I":
            if hasattr(self, "documentopdf"):
                docpdf = self.documentopdf.pdffirma
        else:
            if hasattr(self.documento, "documentoplantilla"):
                docpdf = self.documento.documentoplantilla.documentopdf_set.first()
                if docpdf:
                    docpdf = docpdf.pdffirma
            else:
                print("Documento sin plantilla: ", self.documento.pk)
        if docpdf:
            docpdfstream = io.BytesIO()
            docpdfstream.write(docpdf)
            docpdfR = PdfFileReader(docpdfstream)
            _result = docpdfR.getNumPages()
            docpdfstream.close()
        return _result

    def obtenerNombreDestino(self):
        _result = ""
        if self.tipodestinatario == "UO":
            _result = "%s" % self.periodotrabajo.area.nombrecorto
        elif self.tipodestinatario == "PJ":
            _result = "%s" % (self.personajuridica.nombrecomercial or self.personajuridica.razonsocial)
        elif self.tipodestinatario == "CI":
            _result = "%s" % self.persona.nombrecompleto
        elif self.tipodestinatario == "DP":
            _result = "%s - %s" % (
                self.dependencia.nombrecorto,
                self.dependencia_area_nombre
            )
        return _result

    def DependenciaResponsableCargo(self):
        return self.dependencia_responsable_cargo.nombref if self.dependencia_responsable.sexo == "F" else \
            self.dependencia_responsable_cargo.nombrem

    def obtenerNombreDestinoPersona(self):
        _result = ""
        if self.tipodestinatario == "UO":
            _result = "%s - %s" % (self.obtenerNombreDestino(), self.periodotrabajo.persona.NombreCorto())
        elif self.tipodestinatario == "PJ":
            _result = "%s" % (self.personajuridica.nombrecomercial or self.personajuridica.razonsocial)
        elif self.tipodestinatario == "CI":
            _result = "%s" % self.persona.nombrecompleto
        elif self.tipodestinatario == "DP":
            _result = "%s" % self.dependencia_responsable.nombrecompleto
        return _result

    def ultimafechaderivado(self):
        _result = self.estadosmensajeria.filter(estado='PE').order_by("-creado").first()
        return None if not _result else _result.creado

    def SegDestinoArea(self):
        _result = ""
        if self.tipodestinatario == "UO":
            _result = "%s" % self.periodotrabajo.area.nombre
        elif self.tipodestinatario == "PJ":
            _result = "%s" % (self.personajuridica.nombrecomercial or self.personajuridica.razonsocial)
        elif self.tipodestinatario == "CI":
            _result = "%s" % self.persona.apellidocompleto
        elif self.tipodestinatario == "DP":
            _result = "%s - %s" % (
                self.dependencia.nombrecorto,
                self.dependencia_area_nombre
            )
        return _result

    def SegDestinoNombre(self):
        _result = ""
        if self.tipodestinatario == "UO":
            _result = "%s" % self.periodotrabajo.persona.apellidocompleto
        elif self.tipodestinatario == "PJ":
            _result = "%s" % (self.persona.apellidocompleto if self.persona else "")
        elif self.tipodestinatario == "CI":
            _result = "%s" % self.persona.apellidocompleto
        elif self.tipodestinatario == "DP":
            _result = "%s" % self.dependencia_responsable
        return _result

    def SegOperacionTitulo(self):
        _result = ""
        if self.ultimoestado.estado not in ["NL"]:
            _result = "%s por" % self.ultimoestado.get_estado_display()
        return _result

    def SegOperacionNombre(self):
        # _result = ""
        # if self.ultimoestado.estado not in ["NL"]:
        _result = self.ultimoestado.creador.persona.nombrecompleto
        return _result

    def SegOperacionEstado(self):
        # _result = ""
        # if self.ultimoestado.estado not in ["NL"]:
        _result = self.ultimoestado.get_estado_display()
        return _result

    def SegOperacionFechaTitulo(self):
        _result = ""
        if self.ultimoestado.estado not in ["NL"]:
            _result = "Fecha de %s" % self.ultimoestado.get_estado_display()
        return _result

    def SegOperacionFecha(self):
        _result = ""
        # if self.ultimoestado.estado not in ["NL"]:
        _result = self.ultimoestado.creado
        return _result

    def SegOperacionNotaTitulo(self):
        _result = ""
        if self.ultimoestado.estado not in ["NL"]:
            _result = "Observación de %s" % self.ultimoestado.get_estado_display()
        return _result

    def SegOperacionNota(self):
        _result = ""
        if self.ultimoestado.estado not in ["NL"]:
            _result = self.ultimoestado.observacion
        return _result

    def UltimoEstadoObservado(self):
        _result = self.ultimoestado
        if self.ultimoestado.estado == "LE" and not self.ultimoestado.observacion:
            _result = self.destinoestados.filter(pk__lt=self.ultimoestado.pk).order_by("-creado").first()
        return _result

    def HaRechazado(self):
        return self.destinoestados.filter(estado="RH").count() > 0

    def direccionYreferencia(self):
        _result = self.direccion
        if self.referencia:
            _result = "%s (%s)" % (_result, self.referencia)
        return _result

    def LRevisiones(self):
        _docpdf = None
        if hasattr(self, "documentopdf"):
            _docpdf = self.documentopdf
        else:
            _docpdf = self.documento.documentoplantilla.documentopdf_set.first()
        if _docpdf:
            _revisiones = _docpdf.revisiones.order_by("creado")
        else:
            _revisiones = DocumentoPDF.objects.none()
        return _revisiones


class DestinoEstado(Auditoria):
    ESTADO = [
        ('RG', 'Registrado'),
        ('NL', 'No Leido'),
        ('LE', 'Leido'),
        ('RE', 'Recepcionado'),
        ('RH', 'Rechazado'),
        ('AT', 'Atendido'),
        ('AR', 'Archivado'),
        ('AN', 'Anulado')
    ]
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT, related_name="destinoestados")
    estado = models.CharField(max_length=2, choices=ESTADO, default="RG")
    fecha = models.DateField(null=True, blank=True)
    observacion = models.TextField(max_length=500, blank=True, null=True)

    def __unicode__(self):
        return self.estado

    class Meta:
        verbose_name = 'Estado del Destino'
        verbose_name_plural = 'Estados del Destino'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        pk = self.pk
        super(DestinoEstado, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            dest = self.destino
            dest.ultimoestado = self
            dest.save()
        # Cambiamos el estado del Documento de acuerdo a los estados de los destinos
        documento = self.destino.documento
        documentoestado = None
        destinos = documento.des_documento.exclude(ultimoestado__estado="AN").count()
        destinosanulados = documento.des_documento.filter(ultimoestado__estado="AN").count()
        # if destinos == destinosanulados or documento.ultimoestado.estado == "AN":
        if (destinos == 0 and destinosanulados > 0) or documento.ultimoestado.estado == "AN":
            documentoestado = "AN"
        elif documento.des_documento.filter(ultimoestado__estado__in=["NL", "LE"]).count() == destinos:
            documentoestado = "EM"
        elif documento.des_documento.filter(ultimoestado__estado__in=["AT"]).count() == destinos:
            documentoestado = "AT"
        elif documento.des_documento.filter(ultimoestado__estado__in=["RE"]).count() > 0:
            documentoestado = "RT"
            if documento.des_documento.filter(ultimoestado__estado__in=["RE"]).count() < destinos:
                documentoestado = "RP"
        if documentoestado:
            if documento.ultimoestado.estado != documentoestado:
                DocumentoEstado.objects.create(
                    documento=documento,
                    estado=documentoestado,
                    creador=self.creador
                )


class DestinoEstadoMensajeria(Auditoria):
    ESTADO = [
        ('PE', 'Pendiente'),
        ('RA', 'Recibido Automático'),
        ('RM', 'Recibido Manual'),
        ('DA', 'Devuelto Automático'),  # 48 horas según directiva: Hábiles o NO???
        ('DM', 'Devuelto Manual'),
        ('GN', 'Generado'),
        ('EN', 'Enviado'),
        ('FI', 'Finalizado'),
        ('FD', 'Finalizado Directo'),
        ('NE', 'No Entregado'),
        ('AR', 'Archivado'),
        ('EC', 'Enviado por Correo'),
        ('ED', 'Entrega Directa')
    ]
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT, related_name="estadosmensajeria")
    estado = models.CharField(max_length=2, choices=ESTADO, default="PE")
    fecha = models.DateField(null=True, blank=True)
    observacion = models.TextField(max_length=500, blank=True, null=True)

    def __unicode__(self):
        return self.estado

    class Meta:
        verbose_name = 'Estado Mensajería'
        verbose_name_plural = 'Estados de la Mensajería'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        pk = self.pk
        super(DestinoEstadoMensajeria, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            destino = self.destino
            destino.ultimoestadomensajeria = destino.estadosmensajeria.order_by("-creado").first()
            destino.save()


class DestinoRespuesta(Auditoria):
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT, related_name="respuestas")
    documento = models.ForeignKey(Documento, on_delete=models.PROTECT, related_name="destinoreferencias")

    def __unicode__(self):
        return self.destino.obtenerNombreDestino()

    class Meta:
        verbose_name = 'Respuesta del Destino'
        verbose_name_plural = 'Respuestas del Destino'


class NotificacionElectronica(Auditoria):
    destino = models.ForeignKey(
        Destino, on_delete=models.PROTECT
    )
    correo = models.EmailField()
    asunto = models.CharField(max_length=250)
    mensaje = models.TextField()

    def __unicode__(self):
        return self.destino

    class Meta:
        verbose_name = 'Notificación Electrónica'
        verbose_name_plural = 'Notificaciones Electrónicas'


class CargoInterno(Auditoria):
    ESTADO = [
        ('PE', 'Pendiente'),
        ('ET', 'Entregado'),
        ('EP', 'Entregado Parcial'),
        ('RE', 'Rechazado'),
    ]
    numero = models.IntegerField()
    anio = models.IntegerField()
    observacion = models.CharField(max_length=250)
    archivo = models.BinaryField()
    archivofecha = models.DateField()
    estado = models.CharField(max_length=2, choices=ESTADO)

    def __unicode__(self):
        return "%s - %s" % (
            self.numero,
            self.anio
        )

    class Meta:
        verbose_name = 'Cargo Interno'
        verbose_name_plural = 'Cargos Internos'


class CargoInternoDetalle(Auditoria):
    ESTADO = [
        ('PE', 'Pendiente'),
        ('ET', 'Entregado'),
        ('RE', 'Rechazado'),
    ]
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT, related_name="cargosinternos")
    cargointerno = models.ForeignKey(CargoInterno, on_delete=models.PROTECT, related_name="listadestinos")
    estado = models.CharField(max_length=2, choices=ESTADO)
    periodotrabajo = models.ForeignKey(PeriodoTrabajo, on_delete=models.PROTECT)
    fecha = models.DateField()

    def __unicode__(self):
        return self.estado

    class Meta:
        verbose_name = 'Detalle Cargo Interno'
        verbose_name_plural = 'Detalle de Cargos Internos'


class AmbitoMensajeria(Auditoria):
    CODIGO = [
        ('N', 'Nacional'),
        ('R', 'Regional'),
        ('L', 'Local'),
    ]
    DISTRIBUCION = [
        ('C', 'Currier'),
        ('M', 'Motorizado'),
        ('A', 'Ambos'),
    ]
    codigo = models.CharField(max_length=1, choices=CODIGO, verbose_name="Código")
    orden = models.IntegerField(default=0)
    nombre = models.CharField(max_length=100)
    distribucion = models.CharField(max_length=1, choices=DISTRIBUCION, verbose_name="Distribución")

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Ámbito de Mensajería'
        verbose_name_plural = 'Ámbitos de Mensajería'


class Distribuidor(Auditoria):
    TIPO = [
        ('C', 'Courrier'),
        ('M', 'Motorizado'),
    ]
    tipo = models.CharField(max_length=1, choices=TIPO, default="C")
    inicio = models.DateField()
    fin = models.DateField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    personajuridica = models.ForeignKey(
        PersonaJuridica, on_delete=models.PROTECT, blank=True, null=True,
        related_name="pjdistribuidores", verbose_name=" Persona Jurídica"
    )
    persona = models.ForeignKey(
        Persona, on_delete=models.PROTECT, blank=True, null=True, related_name="pdistribuidores"
    )
    arearindente = models.ForeignKey(Area, null=True, blank=True, on_delete=models.PROTECT)

    objects = AMDistribuidor()

    def __unicode__(self):
        _result = ""
        if self.tipo == "M":
            _result = self.persona.apellidocompleto
        elif self.tipo == "C":
            _result = self.personajuridica.nombrecomercial or self.personajuridica.razonsocial
        return _result

    class Meta:
        verbose_name = 'Distribuidor'
        verbose_name_plural = 'Distribuidores'


class CargoExterno(Auditoria):
    emisorarearindente = models.ForeignKey(Area, null=True, blank=True, on_delete=models.PROTECT)
    emisortrabajador = models.ForeignKey(PeriodoTrabajo, on_delete=models.PROTECT)
    numero = models.IntegerField(verbose_name="Número")
    anio = models.IntegerField(verbose_name="Año")
    fecha = models.DateField()
    distribuidor = models.ForeignKey(Distribuidor, on_delete=models.PROTECT, related_name="cargosexternos")
    ambito = models.ForeignKey(AmbitoMensajeria, on_delete=models.PROTECT, verbose_name="Ámbito")
    nota = models.TextField(blank=True, null=True, verbose_name="Nota")
    cargopdf = models.BinaryField(verbose_name="Cargo en PDF", null=True, blank=True)
    cargofecha = models.DateTimeField(verbose_name="Fecha del Cargo", null=True, blank=True)
    cargoobservacion = models.TextField(blank=True, null=True, verbose_name="Observación del Cargo")
    ultimoestado = models.OneToOneField(
        "CargoExternoEstado", on_delete=models.PROTECT, related_name="ultimoestado", null=True, blank=True
    )

    def __unicode__(self):
        return "%s - %s" % (
            self.numero,
            self.anio
        )

    class Meta:
        verbose_name = 'Cargo Externo'
        verbose_name_plural = 'Cargos Externos'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk:
            if not self.anio:
                self.anio = datetime.datetime.now().year
            if not self.numero:
                if self.emisortrabajador.area.esrindente or self.emisortrabajador.area.rindentepadre:
                    areaemisora = self.emisortrabajador.area.rindentepadre or self.emisortrabajador.area
                    self.emisorarearindente = areaemisora
                    ultce = CargoExterno.objects.filter(
                        emisorarearindente=areaemisora,
                        anio=self.anio
                    ).order_by("-numero").first()
                else:
                    self.emisorarearindente = None
                    ultce = CargoExterno.objects.filter(
                        emisorarearindente__isnull=True,
                        anio=self.anio
                    ).order_by("-numero").first()
                self.numero = (0 if not ultce else ultce.numero) + 1
        super(CargoExterno, self).save(force_insert, force_update, using, update_fields)

    def Numero(self):
        return "%s" % str(self.numero).zfill(4)

    def NumeroFull(self):
        return "%s-%s" % (self.Numero(), self.anio)

    def Nombre(self):
        return "%s" % Distribuidor.objects.get(pk=self.distribuidor.pk).nombre

    def Estado(self):
        return "%s" % self.ultimoestado.get_estado_display()

    def EstadoColor(self):
        _color = ""
        if self.ultimoestado.estado == "GN":
            _color = "primary"
        elif self.ultimoestado.estado == "EN":
            _color = "warning"
        elif self.ultimoestado.estado == "FI":
            _color = "success"
        return _color

    def Dependencia(self):
        _result = self.emisorarearindente
        if _result:
            _result = _result.nombrecorto
        else:
            _result = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]).nombrecorto
        return _result.upper()

    def destinosOrdenReporte(self):
        return self.destinos.order_by(
            "destino__documento__documentotipoarea__documentotipo__nombrecorto",
            "destino__documento__numero",
            "creado"
        )


class CargoExternoEstado(Auditoria):
    ESTADOS = (
        ('GN', 'Generado'),
        ('CE', 'Cerrado'),
        ('FI', 'Finalizado')
    )
    cargoexterno = models.ForeignKey(CargoExterno, on_delete=models.PROTECT, related_name="estados")
    estado = models.CharField(max_length=2, choices=ESTADOS)
    observacion = models.TextField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        return "%s - %s" % (
            self.cargoexterno.Numero(),
            self.estado
        )

    class Meta:
        verbose_name = 'Cargo Externo Estado'
        verbose_name_plural = 'Cargo Externo Estados'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        pk = self.pk
        super(CargoExternoEstado, self).save(force_insert, force_update, using, update_fields)
        if not pk:
            ce = self.cargoexterno
            ce.ultimoestado = self
            ce.save()


class CargoExternoDetalle(Auditoria):
    ESTADO = [
        ('PE', 'Pendiente'),
        ('ET', 'Entregado'),
        ('RE', 'Rechazado'),
    ]

    cargoexterno = models.ForeignKey(
        CargoExterno, on_delete=models.PROTECT, verbose_name="Cargo Externo", related_name="destinos"
    )
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT)
    estado = models.CharField(max_length=2, choices=ESTADO, default="PE")
    ubigeo = models.ForeignKey(Distrito, on_delete=models.PROTECT, related_name="cet_ubigeo", null=True, blank=True)
    direccion = models.CharField(max_length=250, verbose_name="Dirección", null=True, blank=True)
    referencia = models.CharField(max_length=250, blank=True, null=True, verbose_name="Referencia de la Dirección")
    correo = models.EmailField(blank=True, null=True)
    detalle = models.CharField(max_length=200, null=True, blank=True, verbose_name="Detalle")
    cargocomentario = models.CharField(max_length=250, blank=True, null=True, verbose_name="Comentario del Cargo")
    cargopdf = models.BinaryField(verbose_name="Cargo en PDF", null=True, blank=True)
    cargofecha = models.DateTimeField(verbose_name="Fecha del Cargo", null=True, blank=True)
    cargodni = models.CharField(max_length=8, verbose_name="DNI del que firma el cargo", null=True, blank=True)
    cargopersona = models.CharField(max_length=250, blank=True, null=True, verbose_name="Nombre del que firma el cargo")
    cargoparentesco = models.CharField(
        max_length=250, blank=True, null=True, verbose_name="Parentesco del que firma el cargo"
    )
    cargoexpedienteexterno = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Número de Expediente de la Entidad Receptora"
    )

    objects = AMCargoExternoDetalle()

    def __unicode__(self):
        return "%s" % self.destino

    class Meta:
        verbose_name = 'Detalle Cargo Externo'
        verbose_name_plural = 'Detalles Cargo Externo'

    def direccionYreferencia(self):
        if self.direccion:
            _result = self.direccion
            if self.referencia:
                _result = "%s (%s)" % (_result, self.referencia)
            return _result
        else:
            return self.destino.direccionYreferencia()

    def Ubigeo(self):
        return self.ubigeo or self.destino.ubigeo


class Transferencia(Auditoria):
    documento = models.ForeignKey(
        Documento, on_delete=models.PROTECT
    )
    areaorigen = models.ForeignKey(
        "organizacion.Area", on_delete=models.PROTECT, verbose_name="Unidad Organizacional de Origen",
        related_name="tra_origen"
    )
    areadestino = models.ForeignKey(
        "organizacion.Area", on_delete=models.PROTECT, verbose_name="Unidad Organizacional de Destino",
        related_name="tra_destino"
    )
    fecha = models.DateTimeField()
    comentario = models.CharField(max_length=250, blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (
            self.areaorigen,
            self.areadestino
        )

    class Meta:
        verbose_name = 'Transferencia'
        verbose_name_plural = 'Transferencias'
