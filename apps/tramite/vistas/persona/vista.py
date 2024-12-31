"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64

from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import DetailView, FormView, TemplateView
from django_select2.forms import ModelSelect2Widget
from xhtml2pdf import pisa

from apps.inicio.models import Persona
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.vistas.plantillas.hojaenvio import fetch_resources
from modulos.utiles.clases.formularios import AppBaseForm


class PersonaSelectForm(AppBaseForm, forms.Form):
    cbpersona = forms.ModelChoiceField(
        queryset=Persona.objects.order_by("apellidocompleto"),
        widget=ModelSelect2Widget(
            search_fields=["apellidocompleto__icontains"],
            max_results=10
        )
    )


class PersonaVista(TemplateValidaLogin, FormView):
    template_name = "tramite/persona/vista.html"
    form_class = PersonaSelectForm


class PersonaPDFVista(LoginRequiredMixin, TemplateView):
    template_name = "tramite/persona/plantilla.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        postdata = self.request.POST
        persona = Persona.objects.filter(pk=postdata.get("cbpersona", 0)).first()

        if persona:
            response = HttpResponse(content_type=self.content_type)
            response['Content-Disposition'] = 'inline; filename="reporte.pdf"'
            template = get_template(self.template_name)
            context = self.get_context_data(**self.kwargs)
            context["configapp"] = settings.CONFIG_APP
            context["oPer"] = persona
            html = template.render(context)
            pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=fetch_resources, encoding='UTF-8')
            pdfb64 = base64.b64encode(response.getvalue()).decode("utf-8")
            pdfhtml = '<embed ' + \
                      'src="data:application/pdf;base64,{0}" ' + \
                      'type="application/pdf" width="100%" height="600px"/>'
            pdfhtml = pdfhtml.format(pdfb64)
            response = HttpResponse(pdfhtml)
            return response
        return HttpResponse("<strong>Debe elegir la persona</strong>")
