"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Value, BooleanField, Q, Subquery, OuterRef, IntegerField
from django.urls import resolve
from django.views.generic import TemplateView
from rest_framework.authtoken.models import Token

from apps.inicio.models import Tablero
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite import tablas
from apps.tramite.models import Documento, DocumentoFirma, AnexoFirma
from apps.tramite.tablas.mesapartesmensajeria import *
from django.db.models import Value, BooleanField, Q, Case, When, F, Count, CharField, Subquery, OuterRef
from django.db.models.functions import Concat, Cast

from apps.tramite.models import Destino, Documento, DocumentoFirma, AnexoFirma, CargoExternoDetalle, CargoExterno
from modulos.datatable.tables import TableDataMap
from modulos.datatable.views import FeedDataView


class BandejaVista(TemplateValidaLogin, TemplateView):
    http_method_names = "post"

    def get_context_data(self, **kwargs):
        context = super(BandejaVista, self).get_context_data(**kwargs)
        rutaview = resolve(self.request.path)
        tablero = Tablero.objects.filter(
            Q(urloficina=rutaview.view_name)
            |
            Q(urlpersonal=rutaview.view_name)
            |
            Q(urlmesapartes=rutaview.view_name)
        ).first()
        if tablero:
            if tablero.urloficina == rutaview.view_name:
                titulo = tablero.titulooficina
            elif tablero.urlpersonal == rutaview.view_name:
                titulo = tablero.titulopersonal
            else:
                titulo = tablero.titulomesapartes
            context["tituloPagina"] = titulo
        return context


class BandejaListarFeedDataView(FeedDataView):
    table = None
    qs = None
    filter_date = None
    filter_tipodoc = None

    def setup(self, request, *args, **kwargs):
        if self.table:
            self.token = eval(self.table + ".token")
        return super(BandejaListarFeedDataView, self).setup(request, *args, **kwargs)

    def get_queryset(self):
        if self.qs:
            qs = eval(self.qs + "(self.request)")
            filter_date = eval(self.table + ".opts.filter_date")
            filter_tipodoc = eval(self.table + ".opts.filter_tipodoc")
        else:
            qs = super(BandejaListarFeedDataView, self).get_queryset()
            filter_date = self.filter_date
            filter_tipodoc = self.filter_tipodoc
        if filter_date:
            field = filter_date["field"].replace(".", "__")
            inicio = datetime.datetime.strptime(self.request.GET["inicio"], "%d/%m/%Y")
            fin = datetime.datetime.strptime(self.request.GET["fin"], "%d/%m/%Y")
            if qs.count() > 0:
                reg = qs.first()
                # print(type(reg), reg.pk)
                clasefecha = eval("reg." + filter_date["field"] + ".__class__.__name__")
                if clasefecha == "datetime":
                    qs = eval("qs.filter(Q(%s__isnull=True)|Q(%s__date__gte=inicio, %s__date__lte=fin))" % (
                        field, field, field
                    ))
                else:
                    qs = eval("qs.filter(Q(%s__isnull=True)|Q(%s__gte=inicio, %s__lte=fin))" % (
                        field, field, field
                    ))
        if filter_tipodoc and qs.count() > 0:
            tipodoc = self.request.GET.get("tipodoc", "0")
            if tipodoc != "0":
                field = filter_tipodoc["field"].replace(".", "__")
                qs = eval("qs.filter(%s_id=%s)" % (
                    field,
                    tipodoc
                ))
        return qs


# ================= TABLERO  ===================== #
def QueryTableroEntrada(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = Destino.objects.annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        documento__ultimoestado__estado__in=["EM", "RP", "AT", "RT", "RC", "AR"],
        ultimoestado__estado__in=["NL", "LE"]
    ).filter(
        Q(
            Q(
                periodotrabajo__area=periodoactual.area,
                periodotrabajo__esjefe=True
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
        |
        Q(
            periodotrabajo__area=periodoactual.area,
            periodotrabajo__esjefe=False,
            periodotrabajo__persona=periodoactual.persona
        )
    ).order_by("destinoemision")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroRecepcionados(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = Destino.objects.annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        documento__ultimoestado__estado__in=["EM", "RP", "RT", "AT"],
        ultimoestado__estado__in=["RE", "AT", "AR"]
    ).filter(
        Q(
            Q(
                periodotrabajo__area=periodoactual.area,
                periodotrabajo__esjefe=True
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
        |
        Q(
            periodotrabajo__area=periodoactual.area,
            periodotrabajo__esjefe=False,
            periodotrabajo__persona=periodoactual.persona
        )
    ).order_by("creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroEnProyecto(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = Documento.objects.filter(
        ultimoestado__estado__in=["PY", "AN"],
        origentipo__in=["O", "P"]
    ).annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        Q(
            Q(
                origentipo="O",
                responsable__area=periodoactual.area
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
        |
        Q(
            emisor__persona=periodoactual.persona,
            emisor__area=periodoactual.area
        )
        |
        Q(
            # FILTRO DE DOCUMENTOS EN PROYECTO CUANDO EL USUARIO PROYECTA UN DOCUMENTO COMO USUARIO
            esencargado=True,
            origentipo__in=["O", "P"],
            creador=request.user
        )
    ).order_by("-creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroDespacho(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    areactual = periodoactual.area
    _result = Documento.objects.annotate(
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        esencargado=Value(encargado, output_field=BooleanField()),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        ultimoestado__estado__in=["PD", "OF"],
        origentipo__in=["O", "P"]
    ).filter(
        Q(
            Q(
                origentipo="O",
                responsable__area=areactual
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
        |
        Q(
            emisor__persona=periodoactual.persona,
            emisor__area=periodoactual.area
        )
        |
        Q(
            # FILTRO DE DOCUMENTOS EN PROYECTO CUANDO EL USUARIO PROYECTA UN DOCUMENTO COMO USUARIO
            esencargado=True,
            origentipo__in=["O", "P"],
            creador=request.user
        )
    ).order_by("creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroEmitidos(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = Documento.objects.annotate(
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        ultimoestado__estado__in=["EM", "RP", "RT", "AT"],
        origentipo__in=["O", "P"]
    ).filter(
        Q(
            Q(
                origentipo="O",
                responsable__area=periodoactual.area
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
        |
        Q(
            emisor__persona=periodoactual.persona,
            emisor__area=periodoactual.area
        )
        |
        Q(
            esencargado=True,
            origentipo__in=["O", "P"],
            creador=request.user
        )
    ).order_by("-estadoemitido__creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroFirmaVB(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(
        request.session.get("cambioperiodo")
    )
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = DocumentoFirma.objects.annotate(
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        documento__origentipo__in=["O", "P"],
        documento__ultimoestado__estado__in=["PD", "EM", "AT", "RP", "RT", "AR"],
        empleado=periodoactual
    ).order_by("creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroMesaPartesRegistrados(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    _result = Documento.objects.annotate(
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        origentipo__in=['F', 'V'],
        # documento__ultimoestado__estado="PD",
        # estado__codigo="SF",
        # empleado=request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    ).order_by("creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroAnexoFirmaVB(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = AnexoFirma.objects.annotate(
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        # estado="SF",
        empleado=periodoactual
    ).order_by("creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroRechazados(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = Destino.objects.annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        documento__ultimoestado__estado__in=["EM", "RP", "RT", "AT"],
        documento__origentipo__in=["O", "P"],
        ultimoestado__estado__in=["RH"]
    ).filter(
        Q(
            Q(
                documento__origentipo="O",
                documento__responsable__area=periodoactual.area
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
        |
        Q(
            documento__emisor__persona=periodoactual.persona,
            documento__emisor__area=periodoactual.area
        )
    ).order_by("creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


def QueryTableroMiMensajeria(request):
    Token.objects.get_or_create(user=request.user)
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    encargado = periodoactual.EncargaturasOficina().count() > 0
    _result = Destino.objects.annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        esapoyo=Value(periodoactual.esapoyo, output_field=BooleanField()),
        esjefe=Value(periodoactual.esjefe, output_field=BooleanField()),
        esencargado=Value(encargado, output_field=BooleanField()),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).filter(
        documento__ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"],
        ultimoestadomensajeria__isnull=False,
        tipodestinatario__in=["PJ", "CI"]
    ).filter(
        Q(
            documento__origentipo__in=["O", "P"]
        ),
        Q(
            Q(esjefe=True, documento__emisor__area=periodoactual.area)
            |
            Q(esapoyo=True, documento__emisor=periodoactual)
            |
            Q(esapoyo=True, documento__emisor__area=periodoactual.area)
            |
            Q(creador=periodoactual.persona.usuario)
        )
    ).order_by("ultimoestadomensajeria__creado")
    if settings.CONFIG_APP.get("FiltroAnio"):
        _result = _result.filter(
            ultimoestadomensajeria__creado__year=settings.CONFIG_APP.get("FiltroAnio")
        )
    return _result


# ================= OFICINA  ===================== #
# Bandeja de Entrada
def QueryOficinaBandejaEntrada(request):
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    return QueryTableroEntrada(request).filter(
        Q(
            Q(
                periodotrabajo__area=periodoactual.area,
                periodotrabajo__esjefe=True
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
    )


# Recepcionados
def QueryOficinaBandejaRecepcionados(request):
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    return QueryTableroRecepcionados(request).filter(
        Q(
            Q(
                periodotrabajo__area=periodoactual.area,
                periodotrabajo__esjefe=True
            ),
            Q(
                Q(esjefe=True)
                |
                Q(esapoyo=True)
                |
                Q(esencargado=True)
            )
        )
    )


# En Proyecto
def QueryOficinaBandejaEnProyecto(request):
    return QueryTableroEnProyecto(request).filter(
        origentipo="O"
    )


# Despacho
def QueryOficinaBandejaDespacho(request):
    return QueryTableroDespacho(request).filter(
        origentipo="O"
    )


# Emitidos
def QueryOficinaBandejaEmitidos(request):
    return QueryTableroEmitidos(request).filter(
        origentipo="O"
    )


# Firmar o VB
def QueryOficinaBandejaFirmaVB(request):
    return QueryTableroFirmaVB(request).filter(
        Q(empleado__esjefe=True)
        |
        Q(esjefe=True)
        |
        Q(esencargado=True)
    )


# Anexo Firmar o VB
def QueryOficinaAnexoFirmaVB(request):
    return QueryTableroAnexoFirmaVB(request).filter(
        Q(empleado__esjefe=True)
        |
        Q(esencargado=True)
    )


# Rechazados
def QueryOficinaBandejaRechazados(request):
    return QueryTableroRechazados(request).filter(
        documento__origentipo="O"
    )


# Mi Mensajería
def QueryOficinaBandejaMiMensajeria(request):
    return QueryTableroMiMensajeria(request).filter(

    )


# ================= PERSONAL ===================== #
# Bandeja de Entrada
def QueryPersonalBandejaEntrada(request):
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    return QueryTableroEntrada(request).filter(
        periodotrabajo__esjefe=False,
        periodotrabajo__area=periodoactual.area,
        periodotrabajo__persona=request.user.persona
    )


# Recepcionados
def QueryPersonalBandejaRecepcionados(request):
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    return QueryTableroRecepcionados(request).filter(
        periodotrabajo__area=periodoactual.area,
        periodotrabajo__persona=request.user.persona,
        periodotrabajo__esjefe=False
    )


# En Proyecto
def QueryPersonalBandejaEnProyecto(request):
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    return QueryTableroEnProyecto(request).filter(
        origentipo="P",
        responsable__persona=request.user.persona,
        responsable__area=periodoactual.area
    )


# Despacho
def QueryPersonalBandejaDespacho(request):
    return QueryTableroDespacho(request).filter(
        origentipo="P",
        creador=request.user
    )


# Emitidos
def QueryPersonalBandejaEmitidos(request):
    return QueryTableroEmitidos(request).filter(
        origentipo="P"
    )


# Firmar o VB
def QueryPersonalBandejaFirmaVB(request):
    return QueryTableroFirmaVB(request).filter(
        empleado__esjefe=False
    )


# Anexo Firmar o VB
def QueryPersonalAnexoFirmaVB(request):
    return QueryTableroAnexoFirmaVB(request).exclude(
        Q(empleado__esjefe=True)
        # |
        # Q(esencargado=True)
    )


# Rechazados
def QueryPersonalBandejaRechazados(request):
    return QueryTableroRechazados(request).filter(
        documento__origentipo="P"
    )


# ================= MESA DE PARTES ===================== #
# Registrados
def QueryMesaPartesBandejaRegistrados(request):
    return QueryTableroMesaPartesRegistrados(request).filter(
        # periodotrabajo__esjefe=False,
        # periodotrabajo=request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    )


def MensajeriaQueryDestino(request):
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    _result = Destino.objects.exclude(ultimoestado__estado="AN").filter(
        documento__ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"],
        tipodestinatario__in=["PJ", "CI"]
    ).annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).order_by("-ultimoestadomensajeria__creado")
    if not periodoactual.area.esrindente:
        _result = _result.exclude(
            Q(documento__responsable__area__esrindente=True)
            |
            Q(documento__responsable__area__rindentepadre__esrindente=True)
        )
    else:
        _result = _result.filter(
            Q(documento__responsable__area=periodoactual.area)
            |
            Q(documento__responsable__area__rindentepadre=periodoactual.area)
        ).filter(
            Q(documento__documentotipoarea__area__esrindente=True)
            |
            Q(documento__documentotipoarea__area__rindentepadre__esrindente=True)
        )
    return _result


def MensajeriaQueryPlanilados(request):
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    _result = CargoExterno.objects.annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).order_by("creado")

    arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
    if arearindente:
        return _result.filter(
            emisorarearindente=arearindente
        )
    else:
        return _result.filter(
            emisorarearindente__isnull=True
        )


def MensajeriaQueryPlaniladosDetalle(request):
    scheme = request.scheme if hasattr(request, "scheme") else ""
    host = request.get_host() if hasattr(request, "get_host") else ""
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    return CargoExternoDetalle.objects.annotate(
        scheme=Value(scheme),
        host=Value(host),
        token=Value(request.user.auth_token.key),
        trabajadoractual=Value(periodoactual.pk, output_field=IntegerField()),
        usuarioactual=Value(request.user.pk, output_field=IntegerField())
    ).order_by("creado")


# 1. Pendientes
def MensajeriaQueryPE(request):
    return MensajeriaQueryDestino(request).filter(
        ultimoestadomensajeria__estado__in=["PE"]
    )


# 2. Por Enviar
def MensajeriaQueryXE(request):
    return MensajeriaQueryDestino(request).filter(
        ultimoestadomensajeria__estado__in=["RA", "RM"]
    )


# 3. Planillados
def MensajeriaQueryPL(request):
    return MensajeriaQueryPlanilados(request).filter(
        ultimoestado__estado__in=["GN", "CE"]
    )


# 3.1. Detalle de Planillados
def MensajeriaQueryPLD(request):
    return MensajeriaQueryPlaniladosDetalle(request).filter(
        cargoexterno__ultimoestado__estado__in=["GN", "CE"]
    )


# 4. Finalizado
def MensajeriaQueryFI(request):
    return MensajeriaQueryPlanilados(request).filter(
        ultimoestado__estado__in=["FI", "FD"]
    )


# 4.1 Detalle de Finalizado
def MensajeriaQueryFID(request):
    return MensajeriaQueryPlaniladosDetalle(request).filter(
        cargoexterno__ultimoestado__estado__in=["FI", "FD"]
    )


# 5. Finalizado Directo
def MensajeriaQueryFD(request):
    return MensajeriaQueryDestino(request).filter(
        ultimoestadomensajeria__estado__in=["FD"]
    )
