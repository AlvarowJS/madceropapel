"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from io import BytesIO

from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import TemplateView
from xhtml2pdf import pisa

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import PeriodoTrabajo
from apps.tramite.vistas.plantillas.hojaenvio import fetch_resources


class EncargaturaAutorizacionVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        encargatura = PeriodoTrabajo.objects.filter(pk=self.kwargs.get("pk")).first()
        if encargatura:
            context["encargatura"] = encargatura
            template = get_template("tramite/plantillas/encaut.html")
            html = template.render(request=self.request, context=context)
            result = BytesIO()
            pdf = pisa.pisaDocument(html.encode("UTF-8"), dest=result, link_callback=fetch_resources)
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf; charset=utf-8')
                response['Content-Disposition'] = 'inline; filename="encargatura_%s.pdf"' % encargatura.pk
                return response
            else:
                return HttpResponse("<div>%s</div>" % pdf.err)
        return super(EncargaturaAutorizacionVista, self).render_to_response(context, **response_kwargs)


class EncargaturaAnulacionVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        encargatura = PeriodoTrabajo.objects.filter(pk=self.kwargs.get("pk")).first()
        if encargatura:
            context["encargatura"] = encargatura
            template = get_template("tramite/plantillas/encanu.html")
            html = template.render(request=self.request, context=context)
            result = BytesIO()
            pdf = pisa.pisaDocument(html.encode("UTF-8"), dest=result, link_callback=fetch_resources)
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf; charset=utf-8')
                response['Content-Disposition'] = 'inline; filename="encargatura_%s.pdf"' % encargatura.pk
                return response
            else:
                return HttpResponse("<div>%s</div>" % pdf.err)
        return super(EncargaturaAnulacionVista, self).render_to_response(context, **response_kwargs)
