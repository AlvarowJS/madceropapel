"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import DocumentoTipoArea
from apps.tramite.formularios.correlativo import FormCorrelativoSelector, FormCorrelativo
from modulos.utiles.clases.crud import VistaEdicion


class CorrelativoVista(TemplateValidaLogin, TemplateView):
    template_name = "tramite/correlativo/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Correlativos"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = FormCorrelativoSelector()
        # context["tablaTrabajadores"] = TablaTrabajadores()
        return self.render_to_response(context=context)


class CorrelativoListar(TemplateValidaLogin, TemplateView):
    template_name = "tramite/correlativo/lista.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        dta = DocumentoTipoArea.objects.filter(pk=self.kwargs.get("pk")).first()
        if dta:
            context["documentotipoarea"] = dta
            context["form"] = FormCorrelativo(instance=dta)
        return self.render_to_response(context=context)


class CorrelativoCambiar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/correlativo/lista.html"
    model = DocumentoTipoArea
    form_class = FormCorrelativo

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            form.save()
            context["actualizado"] = True
        return self.render_to_response(context)
