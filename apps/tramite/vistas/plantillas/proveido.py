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
from apps.tramite.models import Documento
from apps.tramite.vistas.plantillas.hojaenvio import fetch_resources


class ProveidoVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        documento = Documento.objects.filter(pk=self.kwargs.get("iddoc")).first()
        if documento:
            context["documento"] = documento
            template = get_template("tramite/plantillas/232.html")
            html = template.render(request=self.request, context=context)
            result = BytesIO()
            pdf = pisa.pisaDocument(html.encode("UTF-8"), dest=result, link_callback=fetch_resources, encoding='UTF-8')
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf;')
                response['Content-Disposition'] = 'inline; filename="documento_%s.pdf"' % documento.pk
                return response
            else:
                return HttpResponse("<div>%s</div>" % pdf.err)
        return super(ProveidoVista, self).render_to_response(context, **response_kwargs)
