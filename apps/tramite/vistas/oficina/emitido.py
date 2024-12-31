"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Subquery, OuterRef, Case, When, Value

from apps.tramite.formularios.documentoemitir import FormOficinaEmitidos
from apps.tramite.models import Destino
from apps.tramite.tablas.oficinaemitidos import TablaOficinaEmitidos
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView, BandejaVista


class OficinaBandejaEmitido(BandejaVista):
    template_name = "tramite/oficina/emitido/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["FormOficinaEmitidos"] = FormOficinaEmitidos(request=request)
        context["TablaOficinaEmitidos"] = TablaOficinaEmitidos(request=request)
        return self.render_to_response(context=context)


class OficinaBandejaEmitidosListar(BandejaListarFeedDataView):
    table = "tablas.oficinaemitidos.TablaOficinaEmitidos"
    qs = "QueryOficinaBandejaEmitidos"

    def get_queryset(self):
        qs = super(OficinaBandejaEmitidosListar, self).get_queryset()
        qs = qs.annotate(
            rechazados=Subquery(Destino.objects.filter(
                ultimoestado__estado="RH", documento__pk=OuterRef("pk")
            ).values("ultimoestado__estado")[:1]),
            rechazos=Case(
                When(rechazados__isnull=True, then=Value("")),
                default=Value("rechazado")
            )
        )
        origen = int(self.request.GET.get("origen", "0"))
        if origen > 0:
            qs = qs.filter(responsable__area__id=origen)
        return qs
