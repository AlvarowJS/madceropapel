"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django_select2.views import AutoResponseView

from apps.inicio.formularios.persona import FormAdmPersona
from apps.inicio.models import Persona, Pais
from apps.inicio.tablas.admpersona import TablaAdmPersona
from apps.inicio.vistas.inicio import TemplateValidaLogin
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion


class PersonaListar(AutoResponseView):
    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': self.widget.label_from_instance(obj),
                    'id': obj.pk,
                    'dni': obj.numero
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })


class AdmPersona(TemplateValidaLogin, TemplateView):
    template_name = "inicio/persona/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Administración de Personas"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["tablaAdmPersona"] = TablaAdmPersona()
        return self.render_to_response(context=context)


class AdmPersonaListar(FeedDataView):
    token = TablaAdmPersona.token


class AdmPersonaAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "inicio/persona/formulario.html"
    model = Persona
    form_class = FormAdmPersona

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.confirmado = True
            form.instance.consultadni = timezone.now()
            form.instance.creador = self.request.user
            form.instance.pais = Pais.objects.get(pk=48)
            form.save()
            self.object = form.instance
        return self.render_to_response(self.get_context_data(form=form))


class AdmPersonaEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "inicio/persona/formulario.html"
    model = Persona
    form_class = FormAdmPersona

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.editor = self.request.user
            form.save()
            self.object = form.instance
        return self.render_to_response(self.get_context_data(form=form))
