"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import DestinoEstado
from apps.tramite.tablas.personalrecepcionados import TablaPersonalRecepcionados
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView


class PersonalBandejaRecepcionado(BandejaVista):
    template_name = "tramite/personal/recepcionado/vista.html"

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
        context["TablaPersonalRecepcionados"] = TablaPersonalRecepcionados(request=request, estados=est_ini)
        return self.render_to_response(context=context)


class PersonalBandejaRecepcionadosListar(BandejaListarFeedDataView):
    table = "tablas.personalrecepcionados.TablaPersonalRecepcionados"
    qs = "QueryPersonalBandejaRecepcionados"

    def get_queryset(self):
        qs = super(PersonalBandejaRecepcionadosListar, self).get_queryset()
        estados = self.kwargs.get("estados")
        if estados != "_":
            qs = qs.filter(
                ultimoestado__estado__in=estados.split("_")
            )
        return qs


class PersonalBandejaRecepcionadosAtenderMultiple(TemplateValidaLogin, TemplateView):
    template_name = "tramite/personal/recepcionado/atender.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo")
        request.session["atender"] = {
            "destinos": request.POST.get("ids"),
            "tipo": tipo
        }
        context["urlform"] = reverse("apptra:documento_emitir", kwargs={"tipo": tipo})
        return self.render_to_response(context=context)
