"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.views.generic import TemplateView, FormView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.dependencia import FormMiDependencia
from apps.organizacion.models import Dependencia


class DependenciaInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/dependencia/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Mi Dependencia"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = FormMiDependencia(instance=Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]))
        return self.render_to_response(context=context)


class DependenciaGuardar(FormView):
    template_name = "organizacion/dependencia/formulario.html"
    form_class = FormMiDependencia

    def get_form(self, form_class=None):
        form = super(DependenciaGuardar, self).get_form(form_class)
        form.instance = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.kwargs)
        if form.is_valid():
            form = FormMiDependencia(
                data=self.request.POST,
                instance=Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]),
                files=self.request.FILES
            )
            form.save()
            form = FormMiDependencia(
                instance=Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
            )
            context["save_ok"] = "Los datos se guardaron correctamente"
        context["form"] = form
        return self.render_to_response(context)

    def form_invalid(self, form):
        form = FormMiDependencia(
            data=self.request.POST,
            instance=Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]),
            files=self.request.FILES
        )
        return super(DependenciaGuardar, self).form_invalid(form)
