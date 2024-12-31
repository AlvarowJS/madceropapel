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


class DocumentoDescargarDestVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        doc = Documento.objects.filter(pk=self.kwargs.get("pk")).first()
        if doc:
            context["documento"] = doc
            template = get_template("tramite/plantillas/destinos.html")
            html = template.render(request=self.request, context=context)
            result = BytesIO()
            pdf = pisa.pisaDocument(html.encode("UTF-8"), dest=result, link_callback=fetch_resources)
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf; charset=utf-8')
                response['Content-Disposition'] = 'inline; filename="destinos_%s.pdf"' % doc.nombreDoc()
                return response
            else:
                return HttpResponse("<div>%s</div>" % pdf.err)
        return super(DocumentoDescargarDestVista, self).render_to_response(context, **response_kwargs)
