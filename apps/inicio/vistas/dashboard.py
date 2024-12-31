"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.models import Tablero
from apps.inicio.vistas.inicio import TemplateValidaLogin, Inicio
from apps.tramite.vistas.bandejas import *

MAX_REG_DASH = 5


class Dashboard(Inicio):
    template_name = "inicio/dashboard/vista.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)


class DashboardDatos(TemplateValidaLogin, TemplateView):
    template_name = "inicio/dashboard/lista.html"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        codigo = self.kwargs.get("codigo", None)
        if codigo:
            context["tabobj"] = Tablero.objects.get(codigo=codigo)
            codigo = codigo.replace("db", "")
            data = eval("QueryTablero" + codigo + "(request)")
            if codigo == "FirmaVB":
                data = data.filter(
                    estado__codigo="SF"
                )
            context["maximo"] = MAX_REG_DASH
            context["total"] = data.count()
            context["data"] = data[:MAX_REG_DASH]
        return self.render_to_response(context=context)
