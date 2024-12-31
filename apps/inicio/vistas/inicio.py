"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from datetime import datetime
from pytz import timezone as pytz_timezone

import requests
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.inicio.formularios.bloqueo import FormBloqueo
from apps.inicio.models import Tablero, PersonaTablero
from apps.organizacion.models import PeriodoTrabajo
from apps.tramite.formularios.seguimiento import SeguimientoDirectoForm


class TemplateConfig(object, ):

    def dispatch(self, request, *args, **kwargs):
        # Validamos si la variable de sesión del cambio de periodo aún está vigente
        if request.session.get("cambioperiodo"):
            ptc = PeriodoTrabajo.objects.filter(pk=int(request.session.get("cambioperiodo"))).first()
            if ptc:
                if not ptc.activo or (ptc.fin and ptc.fin < timezone.now()):
                    ptc = None
            if not ptc:
                del request.session["cambioperiodo"]
                return HttpResponse("<script>window.location.href = '%s';</script>" % reverse("appini:inicio"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateConfig, self).get_context_data(**kwargs)
        context["configapp"] = settings.CONFIG_APP
        context["current_domain"] = "://%s" % self.request.get_host()
        context["current_site"] = "%s%s" % (self.request.scheme, context["current_domain"])
        context["anio_actual"] = datetime.now().date().year
        context["anio_anterior"] = datetime.now().date().year - 1
        context["cambioperiodo"] = self.request.session.get("cambioperiodo")
        navegador = self.request.user_agent.browser.family.lower()
        if navegador in settings.CONFIG_APP["CLICKONCE"]:
            context["configbrowser"] = settings.CONFIG_APP["CLICKONCE"][navegador]
        if not self.request.user.is_authenticated:
            usorestante = (settings.CONFIG_APP["FechaInicio"] - timezone.now()).total_seconds()
            if usorestante > 0:
                context["contador"] = settings.CONFIG_APP["FechaInicio"]
        if self.request.user.is_authenticated and hasattr(self.request.user, "persona"):
            if hasattr(self.request.user.persona, "personaconfiguracion"):
                pc = self.request.user.persona.personaconfiguracion
                if pc.certificadovencimiento:
                    context["certificadovencimiento"] = pc.CertificadoVencimientoDias()
                    if pc.CertificadoVencimientoDias() <= settings.CONFIG_APP["TramiteCertificado"]["vencimiento"]:
                        context["certificadoporvencer"] = (pc.CertificadoVencimientoDias() > 0)
                        context["certificadovencido"] = (pc.CertificadoVencimientoDias() <= 0)
                        if pc.certificadoaviso != timezone.now().date():
                            context["certificadoaviso"] = True
                            pc.certificadoaviso = timezone.now().date()
                            pc.save()
            menuprincipal = []
            menuoficina = Tablero.objects.filter(urloficina__isnull=False).order_by("orden")
            menupersonal = Tablero.objects.filter(urlpersonal__isnull=False).order_by("orden")
            # Aqui debemos de filtrar siempre y cuando el area del usuario es Mesa de Partes
            periodotrabajoactual = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            if periodotrabajoactual:
                menumesapartes = Tablero.objects.filter(urlmesapartes__isnull=False).order_by("orden")
                menumesapartes = menumesapartes.exclude(codigo="dbMesaCargos")
                if not periodotrabajoactual.esmensajero or not periodotrabajoactual.area.mensajeria:
                    menumesapartes = menumesapartes.exclude(codigo="dbMesaMensajeria")
                if periodotrabajoactual.permisotramite != "T":
                    menumesapartes = menumesapartes.exclude(codigo="dbMesaRegistrados")
                menuprincipal.append({"titulo": "Mesa de Partes", "codigo": "M", "menus": menumesapartes})
                #
                if menuoficina.count() > 0:
                    menuprincipal.append({"titulo": "Oficina", "codigo": "O", "menus": menuoficina})
                if menupersonal.count() > 0:
                    menuprincipal.append({"titulo": "Profesional", "codigo": "P", "menus": menupersonal})
                context["menuprincipal"] = menuprincipal
                # Verificamos si puede hacer documentos personales
                emisionpersonal = False
                if periodotrabajoactual.area.paracomisiones or \
                        periodotrabajoactual.area == periodotrabajoactual.persona.ultimoperiodotrabajo.area or \
                        periodotrabajoactual.apoyoforma in "T" or \
                        periodotrabajoactual.tipo in "EP" or \
                        (periodotrabajoactual.esjefe and periodotrabajoactual.tipo in ["NN"]) or \
                        (periodotrabajoactual.area != periodotrabajoactual.persona.ultimoperiodotrabajo.area and
                         periodotrabajoactual.tipo in ["EN"]):
                    emisionpersonal = True
                context["emisionpersonal"] = emisionpersonal
            else:
                logout(self.request)
                self.request.session["NoAccess"] = "Ud. no tiene Acceso"
        return context

    # def render_to_response(self, context, **response_kwargs):
    #     if self.request.session.get("NoAccess"):
    #         return HttpResponseRedirect(reverse("appini:inicio_login"))
    #     return super(TemplateConfig, self).render_to_response(context, **response_kwargs)


class TemplateValidaLogin(TemplateConfig, LoginRequiredMixin):
    permitir = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse("<script>window.location.href = '%s';</script>" % reverse("appini:inicio_login"))
        else:
            pass
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateValidaLogin, self).get_context_data(**kwargs)
        context["formBloqueo"] = FormBloqueo()
        return context


class Inicio(TemplateValidaLogin, TemplateView):
    template_name = "inicio/inicio/inicio.html"

    def get_context_data(self, **kwargs):
        context = super(Inicio, self).get_context_data(**kwargs)
        if hasattr(self.request.user, "persona"):
            tableros = Tablero.objects.filter(
                urltablero__isnull=False
            ).order_by("orden")
            for tablero in tableros:
                personatablero = PersonaTablero.objects.filter(
                    persona=self.request.user.persona,
                    tablero=tablero
                ).first()
                if not personatablero:
                    personatablero = PersonaTablero(
                        persona=self.request.user.persona,
                        tablero=tablero,
                        creador=self.request.user,
                        orden=tablero.orden
                    )
                    personatablero.save()
            context["tablero"] = PersonaTablero.objects.filter(
                persona=self.request.user.persona,
                tablero__urltablero__isnull=False
            ).order_by("orden")
            context["form_seg"] = SeguimientoDirectoForm()
        return context


class InicioBlank(TemplateView):
    template_name = "campos/blank.html"


def requestsConsulta(url, user=None, pwd=None, token=None, jsondata=None, data=None, content_type="application/json"):
    jsondata = jsondata or {}
    if jsondata is None:
        jsondata = {}
    headerdata = {
        "Content-Type": content_type
    }
    if user:
        jsondata["User"] = user
    if pwd:
        jsondata["Pwd"] = pwd
    if token:
        headerdata["Authorization"] = "Token %s" % token
    _result = requests.post(url, json=jsondata, headers=headerdata, data=data)
    if _result.ok:
        data = _result.json()
    else:
        data = _result.reason
    return _result.ok, data
