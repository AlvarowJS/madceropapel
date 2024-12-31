"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import os
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import TemplateView
from xhtml2pdf import pisa

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import Documento


class HojaEnvioVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        documento = Documento.objects.filter(pk=self.kwargs.get("iddoc")).first()
        if documento:
            context["documento"] = documento
            template = get_template("tramite/plantillas/304.html")
            html = template.render(request=self.request, context=context)
            result = BytesIO()
            pdf = pisa.pisaDocument(html.encode("UTF-8"), dest=result, link_callback=fetch_resources)
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf; charset=utf-8')
                # response['Content-Disposition'] = 'attachment; filename="noticia_%s.pdf"' % noticia.pk
                response['Content-Disposition'] = 'inline; filename="documento_%s.pdf"' % documento.pk
                return response
            else:
                return HttpResponse("<div>%s</div>" % pdf.err)
        return super(HojaEnvioVista, self).render_to_response(context, **response_kwargs)


def fetch_resources(uri, rel):
    if str(uri).startswith("http"):
        uri2 = uri
    else:
        if os.sep == '\\':
            uri2 = os.sep.join(uri.split('/'))
        else:
            uri2 = uri
        if settings.STATIC_ROOT:
            if uri2.startswith("\static"):
                uri2 = uri2.replace("\static", "", 1)
                predir = settings.STATIC_ROOT
                if predir.__str__() == "./static":
                    predir = settings.STATICFILES_DIRS[0].__str__()
                uri2 = predir + uri2
            elif uri2.startswith("/static/"):
                uri2 = uri2.replace("/static/", "", 1)
                predir = settings.STATIC_ROOT
                uri2 = predir + uri2
        else:
            if uri2.startswith("\static"):
                uri2 = uri2.replace("\static", "", 1)
                uri2 = settings.STATICFILES_DIRS[0].__str__() + uri2
                # uri2 = "file:///" + uri2
                # uri2 = uri2.replace("\\", "//")
                # uri2 = "file:///" + uri2
    return uri2
