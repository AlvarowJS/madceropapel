"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import Documento


class MensajePlantillaDocExt(TemplateValidaLogin, TemplateView):
    template_name = "tramite/mensajes/externo/registrado.html"

    def get_context_data(self, **kwargs):
        context = super(MensajePlantillaDocExt, self).get_context_data(**kwargs)
        context["doc"] = Documento.objects.filter(pk=self.kwargs.get("pk")).first()
        return context
