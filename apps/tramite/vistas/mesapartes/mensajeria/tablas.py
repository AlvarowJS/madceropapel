"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView
from pytz import timezone as pytz_timezone

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import Dependencia
from apps.tramite.formularios.mesapartesenviar import FormAmbitos, FormPllaSelector, FormPllaSelectorF, FormListar
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView
from apps.tramite.tablas.mesapartesmensajeria import *
from apps.tramite.vistas.bandejas import MensajeriaQueryPE, MensajeriaQueryXE, MensajeriaQueryPL, \
    MensajeriaQueryFI, MensajeriaQueryFD

# ===================== QUERY DE TABLAS ==================


MensajeriaBandejas = [
    {"id": "PE", "titulo": "Pendientes"},
    {"id": "XE", "titulo": "Por Enviar"},
    {"id": "PL", "titulo": "Planillados"},
    {"id": "FI", "titulo": "Finalizados"},
    {"id": "FD", "titulo": "Finalizado Directo"}
]


# ========================================================
class MesaPartesMensajeria(BandejaVista):
    template_name = "tramite/mesapartes/mensajeria/vista.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["bandejas"] = MensajeriaBandejas
        return self.render_to_response(context=context)


class MesaPartesMensajeriaTabla(TemplateValidaLogin, TemplateView):
    template_name = "tramite/mesapartes/mensajeria/tabla.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        id = self.kwargs.get("id")
        context["tablaid"] = id
        context["TablaPrincipal"] = eval("TablaMensajeria" + id + "(request)")
        if id == "PE":
            periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            if periodoactual.area.mensajeriahoramaxima:
                context["FormListar"] = FormListar()
        elif id == "XE":
            context["FormAmbitos"] = FormAmbitos()
        elif id == "PL":
            context["FormPllaSelector"] = FormPllaSelector(request=request)
        elif id == "FI":
            context["FormPllaSelectorF"] = FormPllaSelectorF(request=request)
        return self.render_to_response(context=context)


class MesaPartesMensajeriaListar(BandejaListarFeedDataView):

    def setup(self, request, *args, **kwargs):
        _result = super(BandejaListarFeedDataView, self).setup(request, *args, **kwargs)
        id = self.kwargs.get("id")
        self.table = "TablaMensajeria" + id
        self.qs = "MensajeriaQuery" + id
        if id in ["PL", "FI"]:
            self.qs += "D"
        self.token = eval(self.table + ".token")
        return _result

    def get_queryset(self):
        qs = super(MesaPartesMensajeriaListar, self).get_queryset()
        ambito = self.kwargs.get("ambito")
        if self.kwargs.get("id") in "PL":
            if ambito == "N":
                qs = qs.filter(cargoexterno_id=self.kwargs.get("padre"))
            elif ambito != "T":
                qs = qs.filter(pk=-1)
            return qs
        elif self.kwargs.get("id") == "FI":
            if ambito == "N":
                qs = qs.filter(cargoexterno_id=self.kwargs.get("padre"))
            elif ambito != "T":
                qs = qs.filter(pk=-1)
            return qs
        else:
            periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            if self.kwargs.get("id") == "PE" and self.request.GET.get("listado", "T") == "D" and \
                periodoactual.area.mensajeriahoramaxima:
                fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
                if fechaActual.time() >= periodoactual.area.mensajeriahoramaxima:
                    # print(fechaActual.combine(fechaActual.date(), periodoactual.area.mensajeriahoramaxima))
                    fechaMaxima = timezone.make_aware(
                        fechaActual.combine(fechaActual.date(), periodoactual.area.mensajeriahoramaxima)
                    )
                    # print(fechaMaxima)
                    qs = qs.filter(
                        # documento__estadoemitido__creado__lte=fechaMaxima,
                        ultimoestadomensajeria__creado__lte=fechaMaxima
                    )
            if not periodoactual.area.esrindente:
                qs = qs.exclude(
                    Q(documento__responsable__area__esrindente=True)
                    |
                    Q(documento__responsable__area__rindentepadre__esrindente=True)
                )
            else:
                qs = qs.filter(
                    Q(documento__responsable__area=periodoactual.area)
                    |
                    Q(documento__responsable__area__rindentepadre=periodoactual.area)
                ).filter(
                    Q(documento__documentotipoarea__area__esrindente=True)
                    |
                    Q(documento__documentotipoarea__area__rindentepadre__esrindente=True)
                )
            if ambito:
                distritoDep = periodoactual.area.mensajeriadistritos
                if distritoDep:
                    distritoDep = eval(distritoDep)
                else:
                    distritoDep = [Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]).ubigeo.pk]
                if ambito in ["L", "R"]:
                    if ambito == "L":
                        qs = qs.filter(
                            ubigeo_id__in=distritoDep
                        )
                    elif ambito == "R":
                        qs = qs.filter(
                            ubigeo__provincia__departamento=periodoactual.area.dependencia.ubigeo.provincia.departamento,
                        ).exclude(
                            ubigeo_id__in=distritoDep
                        )
                elif ambito == "N":
                    qs = qs.exclude(
                        Q(ubigeo__provincia__departamento=periodoactual.area.dependencia.ubigeo.provincia.departamento)
                    )
            # return qs.order_by("documento__estadoemitido__creado")
            return qs.order_by("ultimoestadomensajeria__creado")

    def get_context_data(self, **kwargs):
        context = super(MesaPartesMensajeriaListar, self).get_context_data(**kwargs)
        context["totales"] = dict()
        for bandeja in MensajeriaBandejas:
            id = bandeja["id"]
            context["totales"][id] = eval("MensajeriaQuery" + id + "(self.request).count()")
        return context
