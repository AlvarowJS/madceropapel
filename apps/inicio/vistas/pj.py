"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.formularios.pj import formPJSelector, PJForm
from apps.inicio.models import PersonaJuridica
from apps.inicio.tablas.pj import TablaPJ
from apps.inicio.vistas.inicio import TemplateValidaLogin
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion


class PJVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/pj/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Personas Jurídicas"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["formPJSelector"] = formPJSelector()
        context["tablaPJ"] = TablaPJ()
        return self.render_to_response(context=context)


class PJListar(FeedDataView):
    token = TablaPJ.token

    def get_queryset(self):
        qs = super(PJListar, self).get_queryset()
        qs = qs.filter(
            tipo=self.kwargs.get("modo")
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(PJListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("ruc")
        return qs


class PJAgregar(VistaCreacion):
    template_name = "inicio/pj/formulario.html"
    model = PersonaJuridica
    form_class = PJForm

    def get_form_class(self):
        form_class = super(PJAgregar, self).get_form_class()
        if self.kwargs.get("modo") == "O":
            form_class.firstfield = "razonsocial"
        elif self.kwargs.get("modo") == "R":
            form_class.firstfield = "ruc"
        return form_class

    def get_form(self, form_class=None):
        form = super(PJAgregar, self).get_form(form_class)
        if self.kwargs.get("modo") == "O":
            del form.fields["ruc"]
            del form.fields["nombrecomercial"]
        form.fields["pais"].initial = [48]
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            form.instance.confirmado = True
            form.instance.creador = self.request.user
            form.instance.tipo = self.kwargs.get("modo")
            form.save()
        context["form"] = form
        return self.render_to_response(context)


class PJEditar(VistaEdicion):
    template_name = "inicio/pj/formulario.html"
    model = PersonaJuridica
    form_class = PJForm

    def get_form_class(self):
        form_class = super(PJEditar, self).get_form_class()
        if self.get_object().tipo == "O":
            form_class.firstfield = "razonsocial"
        elif self.get_object().tipo == "R":
            form_class.firstfield = "ruc"
        return form_class

    def get_form(self, form_class=None):
        form = super(PJEditar, self).get_form(form_class)
        if self.get_object().tipo == "O":
            del form.fields["ruc"]
            del form.fields["nombrecomercial"]
        form.fields["pais"].initial = [48]
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            form.instance.editor = self.request.user
            form.save()
        context["form"] = form
        return self.render_to_response(context)


class PJEliminar(VistaEliminacion):
    template_name = "inicio/pj/eliminar.html"
    model = PersonaJuridica
