"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.tramite.formularios.documentoproyecto import FormTablaPersonalEnProyecto
from apps.tramite.tablas.personalenproyecto import TablaPersonalEnProyecto
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView


class PersonalBandejaEnProyecto(BandejaVista):
    template_name = "tramite/personal/enproyecto/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["FormTablaPersonalEnProyecto"] = FormTablaPersonalEnProyecto()
        context["TablaPersonalEnProyecto"] = TablaPersonalEnProyecto(request=request)
        return self.render_to_response(context=context)


class PersonalBandejaEnProyectoListar(BandejaListarFeedDataView):
    table = "tablas.personalenproyecto.TablaPersonalEnProyecto"
    qs = "QueryPersonalBandejaEnProyecto"

    def get_queryset(self):
        query = super(PersonalBandejaEnProyectoListar, self).get_queryset()
        modo = self.request.GET.get("modo")
        if modo == "PY":
            query = query.filter(
                ultimoestado__estado="PY"
            )
        elif modo == "AN":
            query = query.filter(
                ultimoestado__estado="AN"
            )
        return query
