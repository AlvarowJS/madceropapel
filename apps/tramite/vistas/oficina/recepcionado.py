"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Value, Subquery, OuterRef, DateTimeField
from django.urls import reverse
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import DestinoEstado
from apps.tramite.tablas.oficinarecepcionados import TablaOficinaRecepcionados
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView, BandejaVista


class OficinaBandejaRecepcionado(BandejaVista):
    template_name = "tramite/oficina/recepcionado/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        est_ini = "RE"
        lestados = [("T", "Todo")]
        for estado in DestinoEstado.ESTADO:
            if estado[0] in ["RE", "RH", "AT", "AR"]:
                nestado = list(estado)
                if estado[0] in est_ini:
                    nestado += ["selected"]
                lestados.append(nestado)
        context["TablaEstados"] = lestados
        context["TablaOficinaRecepcionados"] = TablaOficinaRecepcionados(request=request, estados=est_ini)
        return self.render_to_response(context=context)


class OficinaBandejaRecepcionadosListar(BandejaListarFeedDataView):
    table = "tablas.oficinarecepcionados.TablaOficinaRecepcionados"
    qs = "QueryOficinaBandejaRecepcionados"

    def get_queryset(self):
        qs = super(OficinaBandejaRecepcionadosListar, self).get_queryset().annotate(
            token=Value(self.request.user.auth_token.key)
        )
        estados = self.kwargs.get("estados")
        if estados != "_":
            qs = qs.filter(
                ultimoestado__estado__in=estados.split("_")
            )
        return qs

    def sort_queryset(self, queryset):
        qs = super(OficinaBandejaRecepcionadosListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            # qs = qs.order_by("fecha_recibido")
            qs = qs.order_by("ultimoestado__creado")
        return qs


class OficinaBandejaRecepcionadosAtender(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/recepcionado/atender.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo")
        request.session["atender"] = {
            "destinoid": self.kwargs.get("id"),
            "tipo": tipo
        }
        context["urlform"] = reverse("apptra:documento_emitir", kwargs={"tipo": tipo})
        return self.render_to_response(context=context)


class OficinaBandejaRecepcionadosAtenderMultiple(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/recepcionado/atender.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo")
        forma = self.kwargs.get("forma")
        request.session["atender"] = {
            "destinos": request.POST.get("ids"),
            "tipo": tipo,
            "forma": forma
        }
        context["urlform"] = reverse("apptra:documento_emitir", kwargs={"tipo": tipo})
        return self.render_to_response(context=context)
