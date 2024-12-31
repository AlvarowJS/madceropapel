"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.inicio.managers import AMPersona, AMPersonaJuridica
from modulos.utiles.clases.formularios import Auditoria, EstadosSiNo


class Anio(Auditoria):
    id = models.IntegerField(primary_key=True)
    numero = models.IntegerField()
    denominacion = models.CharField(max_length=200)
    nombredecenio = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return self.denominacion

    class Meta:
        verbose_name = 'Año'
        verbose_name_plural = 'Años'
        indexes = [
            models.Index(fields=["numero"])
        ]


class Pais(Auditoria):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)
    nacionalidad = models.CharField(max_length=50, blank=True)
    iso2 = models.CharField(max_length=10, null=True, blank=True)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Paises'
        indexes = [
            models.Index(fields=["nombre"])
        ]


class Departamento(Auditoria):
    id = models.IntegerField(primary_key=True)
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=2, unique=True)
    nombre = models.CharField(max_length=100)

    def __unicode__(self):
        return "%s" % self.nombre

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["codigo"]
        indexes = [
            models.Index(fields=["nombre"])
        ]

    @staticmethod
    def get_absolute_url():
        return ""


class Provincia(Auditoria):
    id = models.IntegerField(primary_key=True)
    codigo = models.CharField(max_length=4, unique=True)
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    capital = models.CharField(max_length=100, blank=True, null=True)
    latitud = models.DecimalField(max_digits=20, decimal_places=16, blank=True, null=True)
    longitud = models.DecimalField(max_digits=20, decimal_places=16, blank=True, null=True)
    puntocentral = models.CharField(max_length=200, blank=True, null=True)
    poligonal = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s" % self.nombre

    class Meta:
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"
        ordering = ["codigo"]
        indexes = [
            models.Index(fields=["nombre"])
        ]

    @staticmethod
    def get_absolute_url():
        return ""


class Distrito(Auditoria):
    id = models.IntegerField(primary_key=True)
    codigo = models.CharField(max_length=6, unique=True)
    nombre = models.CharField(max_length=100)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    latitud = models.DecimalField(max_digits=20, decimal_places=16, blank=True, null=True)
    longitud = models.DecimalField(max_digits=20, decimal_places=16, blank=True, null=True)
    poligonal = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s" % self.nombre

    class Meta:
        verbose_name = "Distrito"
        verbose_name_plural = "Distritos"
        ordering = ["codigo"]
        indexes = [
            models.Index(fields=["nombre"])
        ]

    @staticmethod
    def get_absolute_url():
        return ""

    def Departamento(self):
        return self.provincia.departamento.nombre

    def RutaProvincia(self):
        return "%s / %s" % (self.provincia.nombre, self.nombre)

    def RutaDepartamento(self):
        return "%s / %s / %s" % (self.provincia.departamento.nombre, self.provincia.nombre, self.nombre)


class Cargo(Auditoria):
    id = models.IntegerField(primary_key=True)
    nombrem = models.CharField(max_length=150, verbose_name="Nombre Masculino")
    nombref = models.CharField(max_length=150, verbose_name="Nombre Femenino")
    nombrecorto = models.CharField(max_length=30, verbose_name="Nombre Corto")
    paraunidad = models.BooleanField(default=True, verbose_name="Para Unidad Organizacional")
    paracomision = models.BooleanField(default=False, verbose_name="Para Comisión")
    esprincipal = models.BooleanField(default=False, verbose_name="Es Principal")
    esapoyo = models.BooleanField(default=False, verbose_name="Es Apoyo")

    def __unicode__(self):
        return self.nombrecorto

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        indexes = [
            models.Index(fields=["nombrem"]),
            models.Index(fields=["nombref"]),
            models.Index(fields=["nombrecorto"]),
        ]


class TipoDocumentoIdentidad(Auditoria):
    codigo = models.CharField(max_length=3, verbose_name="Código")
    nombre = models.CharField(max_length=30, verbose_name="Nombre")
    codigosunat = models.CharField(max_length=2, verbose_name="Código SUNAT", default="")
    abreviatura = models.CharField(max_length=10, verbose_name="Abreviatura")
    longitud = models.IntegerField(default=10, verbose_name="Longitud")
    exacto = models.BooleanField(default=False)
    tipo = models.CharField(max_length=1, default="A")
    buscareniec = models.BooleanField(default=False)
    buscasunat = models.BooleanField(default=False)
    parapersona = models.BooleanField(default=False)

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Tipo Documento'
        verbose_name_plural = 'Tipos Documento'
        indexes = [
            models.Index(fields=["nombre"])
        ]


class TipoFirma(Auditoria):
    id = models.IntegerField(primary_key=True)
    codigo = models.CharField(max_length=2, verbose_name="Código")
    nombre = models.CharField(max_length=20, verbose_name="Nombre")

    def __unicode__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Tipo de Firma'
        verbose_name_plural = 'Tipos de Firma'
        indexes = [
            models.Index(fields=["nombre"])
        ]


class Persona(Auditoria):
    SEXO = [
        ('M', 'MASCULINO'),
        ('F', 'FEMENINO'),
    ]
    tipodocumentoidentidad = models.ForeignKey(TipoDocumentoIdentidad, on_delete=models.PROTECT)
    numero = models.CharField(max_length=15)
    paterno = models.CharField(max_length=50, verbose_name="Apellido Paterno")
    materno = models.CharField(max_length=50, verbose_name="Apellido Materno")
    nombres = models.CharField(max_length=50, verbose_name="Nombres")
    nombrecompleto = models.CharField(max_length=250, verbose_name="Nombre Completo")
    apellidocompleto = models.CharField(max_length=250, verbose_name="Apellido Completo")
    alias = models.CharField(max_length=50, verbose_name="Alias", default="")
    sexo = models.CharField(max_length=1, choices=SEXO)
    nacimiento = models.DateField(verbose_name="Fecha de Nacimiento", null=True, blank=True)
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT)
    ubigeo = models.ForeignKey(Distrito, on_delete=models.PROTECT, blank=True, null=True)
    direccion = models.CharField(max_length=250, blank=True, null=True, verbose_name="Dirección")
    referencia = models.CharField(max_length=250, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    ultimocargo = models.CharField(max_length=200, blank=True, null=True, verbose_name="Último Cargo")
    correo = models.EmailField(blank=True, null=True)
    confirmado = models.BooleanField(default=False, choices=EstadosSiNo)
    ultimoperiodotrabajo = models.ForeignKey(
        'organizacion.PeriodoTrabajo', on_delete=models.PROTECT, blank=True, null=True,
        verbose_name="Último Periodo de Trabajo", related_name="personaanterior"
    )
    consultadni = models.DateTimeField(blank=True, null=True)
    usuario = models.OneToOneField(User, on_delete=models.PROTECT, null=True, blank=True)
    cambiaclave = models.BooleanField(default=True)
    fotografia = models.BinaryField(null=True, blank=True)

    objects = AMPersona()

    def __unicode__(self):
        return self.nombrecompleto

    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        unique_together = [
            "tipodocumentoidentidad",
            "numero"
        ]
        indexes = [
            models.Index(fields=["numero"]),
            models.Index(fields=["nombrecompleto"]),
            models.Index(fields=["apellidocompleto"]),
        ]

    def periodotrabajoactual(self, idpt=None):
        idpt = idpt or self.ultimoperiodotrabajo.pk
        _result = self.TrabajosActivos().filter(pk=idpt).first()
        _encargos = self.TrabajosActivos().filter(tipo__in=["EN", "EP"]).first()
        if _encargos:
            if _encargos.area == _result.area:
                _result = _encargos
        return _result

    def terminacion_genero(self):
        result = ""
        if self.sexo:
            result = 'o' if self.sexo == "M" else 'a'
        return result

    def nombreDestino(self):
        return "%s %s, %s" % (
            self.paterno.upper(),
            self.materno.upper(),
            self.nombres
        )

    def apellidos(self):
        _result = "%s %s" % (
            self.paterno.upper(),
            self.materno.upper()
        )
        return _result.strip()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, update_pt=True):
        self.nombrecompleto = "%s %s %s" % (
            self.nombres,
            self.paterno,
            self.materno
        )
        self.nombrecompleto = self.nombrecompleto.replace("  ", " ").strip()
        self.apellidocompleto = "%s %s %s" % (
            self.paterno,
            self.materno,
            self.nombres
        )
        self.apellidocompleto = self.apellidocompleto.replace("  ", " ").strip()
        self.alias = "%s%s" % (self.nombres[0], self.paterno)
        if update_pt:
            self.ultimoperiodotrabajo = self.trabajos.filter(
                tipo="NN", area__paracomisiones=False
            ).order_by("-pk").first()
        if not self.numero and self.tipodocumentoidentidad.codigo == "OTR":
            ultreg = Persona.objects.filter(tipodocumentoidentidad__codigo="OTR").order_by("-numero").first()
            numero = 0
            if ultreg:
                numero = int(ultreg.numero[1:])
            self.numero = "O%s" % str(numero + 1).zfill(9)
        super(Persona, self).save(force_insert, force_update, using, update_fields)
        if not hasattr(self, "personaconfiguracion"):
            PersonaConfiguracion.objects.create(persona=self, creador=self.creador, cambiarpassword=True)

    def NombreCorto(self):
        return "%s %s" % (self.nombres.split(" ")[0], self.paterno)

    def TrabajosActivos(self, idactual=None):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        _result = self.trabajos.filter(
            activo=True,
            inicio__lte=fechaActual
        ).filter(
            Q(fin__gte=fechaActual)
            |
            Q(fin__isnull=True)
        ).filter(
            Q(tipo__in=["NN", "EP", "AP"])
            |
            Q(
                tipo__in=["EN"],
                encargaturaplantilla__isnull=False,
                encargaturaplantillaanulacion__isnull=True
            )
        ).order_by("area__paracomisiones", "area__nombre")
        return _result

    def CiudadanoUltimoCargo(self):
        __cargo = ""
        from apps.tramite.models import Documento
        registroDoc = self.emisorendocumento.order_by("-pk").first()
        if registroDoc:
            __cargo = registroDoc.ciudadanocargo
        return __cargo

    def ReiniciarPassword(self):
        if self.usuario:
            if not self.usuario.is_staff or settings.CONFIG_APP.get("EnDesarrollo"):
                usuario = self.usuario
                usuario.set_password(self.numero)
                usuario.save()
                perconf = self.personaconfiguracion
                perconf.cambiarpassword = True
                perconf.save(update_email=False)

    def Encargaturas(self):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        return self.trabajos.filter(
            Q(tipo='EP', aprobador__isnull=False)
            |
            Q(tipo='EN', encargaturaplantilla__isnull=False)
        ).filter(
            Q(activo=0)
            |
            Q(fin__lt=fechaActual)
        )


class PersonaConfiguracion(Auditoria):
    persona = models.OneToOneField(Persona, on_delete=models.PROTECT)
    menuabierto = models.BooleanField(default=False)
    correoinstitucional = models.EmailField(null=True, blank=True)
    usuariodominio = models.CharField(max_length=50, null=True, blank=True)
    bloqueado = models.BooleanField(default=False)
    cambiarpassword = models.BooleanField(default=False)
    certificadovencimiento = models.DateTimeField(null=True, blank=True, verbose_name="Vencimiento de Certificado")
    certificadoaviso = models.DateField(null=True, blank=True, verbose_name="Aviso de Vencimiento de Certificado")

    def __unicode__(self):
        return self.persona.nombrecompleto

    class Meta:
        verbose_name = 'Configuración de Persona'
        verbose_name_plural = 'Configuraciones de Persona'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, update_email=True):
        super(PersonaConfiguracion, self).save(force_insert, force_update, using, update_fields)
        if self.persona.usuario and self.correoinstitucional and update_email:
            usuario = self.persona.usuario
            usuario.email = self.correoinstitucional
            usuario.save()

    def CertificadoVencimientoDias(self):
        return (self.certificadovencimiento - timezone.now()).days

    def CertificadoVencimientoColor(self):
        _color = "light"
        if self.CertificadoVencimientoDias() <= 0:
            _color = "danger"
        elif self.CertificadoVencimientoDias() <= settings.CONFIG_APP["TramiteCertificado"]["vencimiento"]:
            _color = "warning"
        return _color


class PersonaJuridica(Auditoria):
    TIPOS = [
        ("R", "RUC"),
        ("O", "Otro"),
    ]
    tipo = models.CharField(max_length=1, default="R", verbose_name="Tipo", choices=TIPOS)
    ruc = models.CharField(max_length=11)
    razonsocial = models.CharField(max_length=250, verbose_name="Razón Social")
    nombrecomercial = models.CharField(max_length=250, verbose_name="Nombre Comercial", null=True, blank=True)
    direccion = models.CharField(max_length=250, blank=True, null=True, verbose_name="Dirección")
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT)
    ubigeo = models.ForeignKey(Distrito, on_delete=models.PROTECT, blank=True, null=True)
    referencia = models.CharField(max_length=250, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    representante = models.ForeignKey(
        Persona, verbose_name="Representante Legal", blank=True, null=True, on_delete=models.PROTECT
    )
    representantecargo = models.CharField(
        max_length=250, verbose_name="Cargo Representante Legal", blank=True, null=True
    )
    confirmado = models.BooleanField(default=False)
    interopera = models.BooleanField(default=False)
    consultaruc = models.DateField(blank=True, null=True)

    objects = AMPersonaJuridica()

    def __unicode__(self):
        return self.nombrecomercial or self.razonsocial

    class Meta:
        verbose_name = 'Persona Jurídica'
        verbose_name_plural = 'Personas Jurídicas'
        unique_together = [
            "tipo", "ruc"
        ]
        indexes = [
            models.Index(fields=["ruc"]),
            models.Index(fields=["razonsocial"]),
            models.Index(fields=["nombrecomercial"]),
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.tipo == "O" and not self.ruc:
            ultruc = PersonaJuridica.objects.filter(tipo="O").order_by("-ruc").first()
            ultruc = 0 if not ultruc else int(ultruc.ruc[1:])
            self.ruc = "O%s" % str(ultruc + 1).zfill(10)
        super(PersonaJuridica, self).save(force_insert, force_update, using, update_fields)


class Tablero(Auditoria):
    codigo = models.CharField(max_length=20)
    titulo = models.CharField(max_length=100)
    titulooficina = models.CharField(max_length=100, default="")
    titulopersonal = models.CharField(max_length=100, default="")
    titulomesapartes = models.CharField(max_length=100, default="")
    urltablero = models.CharField(max_length=100, null=True, blank=True)
    orden = models.IntegerField(default=0)
    verpdf = models.BooleanField(default=False)
    color = models.CharField(max_length=50, default="")
    icono = models.CharField(max_length=50, default="")
    verfirmavb = models.BooleanField(default=False)
    urloficina = models.CharField(max_length=100, null=True, blank=True)
    urlpersonal = models.CharField(max_length=100, null=True, blank=True)
    urlmesapartes = models.CharField(max_length=100, null=True, blank=True)
    vercontador = models.BooleanField(default=False)

    def __unicode__(self):
        return self.codigo

    class Meta:
        verbose_name = 'Tablero'
        verbose_name_plural = 'Tableros'


class PersonaTablero(Auditoria):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT)
    tablero = models.ForeignKey(Tablero, on_delete=models.PROTECT)
    visible = models.BooleanField(default=True)
    expandido = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)

    def __unicode__(self):
        return self.persona.nombrecompleto

    class Meta:
        verbose_name = 'Tablero de Persona'
        verbose_name_plural = 'Tableros de Persona'

# class Mensaje(Auditoria):
#     inicio = models.DateTimeField()
#     fin = models.DateTimeField()
#     titulo = models.CharField(max_length=50)
#     contenido = models.TextField()
#     estado = models.BooleanField(default=True)
#
#     def __unicode__(self):
#         return self.titulo
#
#     class Meta:
#         verbose_name = 'Mensaje'
#         verbose_name_plural = 'Mensajes'
#
#
# class MensajeLectura(Auditoria):
#     mensaje = models.ForeignKey(Mensaje, on_delete=models.PROTECT)
#
#     def __unicode__(self):
#         return self.mensaje.titulo
#
#     class Meta:
#         verbose_name = 'Lectura de Mensaje'
#         verbose_name_plural = 'Lecturas de Mensaje'
