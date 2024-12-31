"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.tablas.oficinaanexofirma import TablaOficinaAnexoFirmaVB
from apps.tramite.tablas.oficinafirma import TablaOficinaFirmaVB
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView, BandejaVista


class OficinaBandejaFirma(BandejaVista):
    template_name = "tramite/oficina/firma/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["TablaOficinaFirmaVB"] = TablaOficinaFirmaVB(request=request)
        context["TablaOficinaAnexoFirmaVB"] = TablaOficinaAnexoFirmaVB(request=request)
        return self.render_to_response(context=context)


class OficinaBandejaFirmaVBListar(BandejaListarFeedDataView):
    table = "tablas.oficinafirma.TablaOficinaFirmaVB"
    qs = "QueryOficinaBandejaFirmaVB"

    def get_queryset(self):
        qs = super(OficinaBandejaFirmaVBListar, self).get_queryset()
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
