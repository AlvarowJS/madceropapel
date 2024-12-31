"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.formularios.documentoproyecto import FormTablaOficinaEnProyecto
from apps.tramite.tablas.oficinaenproyecto import TablaOficinaEnProyecto
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView, BandejaVista


class OficinaBandejaEnProyecto(BandejaVista):
    template_name = "tramite/oficina/enproyecto/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["FormTablaOficinaEnProyecto"] = FormTablaOficinaEnProyecto(request)
        context["TablaOficinaEnProyecto"] = TablaOficinaEnProyecto(request=request)
        return self.render_to_response(context=context)


class OficinaBandejaEnProyectoListar(BandejaListarFeedDataView):
    table = "tablas.oficinaenproyecto.TablaOficinaEnProyecto"
    qs = "QueryOficinaBandejaEnProyecto"

    def get_queryset(self):
        query = super(OficinaBandejaEnProyectoListar, self).get_queryset()
        modo = self.request.GET.get("modo")
        if modo == "PY":
            query = query.filter(
                ultimoestado__estado="PY"
            )
        elif modo == "AN":
            query = query.filter(
                ultimoestado__estado="AN"
            )
        origen = int(self.request.GET.get("origen", "0"))
        if origen > 0:
            query = query.filter(responsable__area__id=origen)
        return query
