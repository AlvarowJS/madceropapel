"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.tablas.personalanexofirma import TablaPersonalAnexoFirmaVB
from apps.tramite.tablas.personalfirma import TablaPersonalFirmaVB
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView


class PersonalBandejaFirma(BandejaVista):
    template_name = "tramite/personal/firma/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["TablaPersonalFirmaVB"] = TablaPersonalFirmaVB(request=request)
        context["TablaPersonalAnexoFirmaVB"] = TablaPersonalAnexoFirmaVB(request=request)
        return self.render_to_response(context=context)


class PersonalBandejaFirmaVBListar(BandejaListarFeedDataView):
    table = "tablas.personalfirma.TablaPersonalFirmaVB"
    qs = "QueryPersonalBandejaFirmaVB"

    def get_queryset(self):
        qs = super(PersonalBandejaFirmaVBListar, self).get_queryset()
        modo = self.kwargs.get("modo")
        if modo == "fi":
            qs = qs.filter(
                estado__codigo="FI"
            )
        elif modo == "sf":
            qs = qs.filter(
                estado__codigo="SF"
            )
        else:
            qs = qs.filter(
                estado__codigo="XX"
            )
        return qs
