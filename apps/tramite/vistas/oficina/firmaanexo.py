"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.vistas.bandejas import BandejaListarFeedDataView


class OficinaAnexoFirmaVBListar(BandejaListarFeedDataView):
    table = "tablas.oficinaanexofirma.TablaOficinaAnexoFirmaVB"
    qs = "QueryOficinaAnexoFirmaVB"

    def get_queryset(self):
        qs = super(OficinaAnexoFirmaVBListar, self).get_queryset()
        modo = self.kwargs.get("modo")
        if modo == "fi":
            qs = qs.filter(
                estado="FI"
            )
        elif modo == "sf":
            qs = qs.filter(
                estado="SF"
            )
        else:
            qs = qs.filter(
                estado="XX"
            )
        return qs
