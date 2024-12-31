"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Subquery, OuterRef, Case, When, Value

from apps.tramite.models import Destino
from apps.tramite.tablas.personalemitidos import TablaPersonalEmitidos
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView


class PersonalBandejaEmitido(BandejaVista):
    template_name = "tramite/personal/emitido/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["TablaPersonalEmitidos"] = TablaPersonalEmitidos(request=request)
        return self.render_to_response(context=context)


class PersonalBandejaEmitidosListar(BandejaListarFeedDataView):
    table = "tablas.personalemitidos.TablaPersonalEmitidos"
    qs = "QueryPersonalBandejaEmitidos"

    def get_queryset(self):
        qs = super(PersonalBandejaEmitidosListar, self).get_queryset()
        qs = qs.annotate(
            rechazados=Subquery(Destino.objects.filter(
                ultimoestado__estado="RH", documento__pk=OuterRef("pk")
            ).values("ultimoestado__estado")[:1]),
            rechazos=Case(
                When(rechazados__isnull=True, then=Value("")),
                default=Value("rechazado")
            )
        )
        return qs
