"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64

from django.conf import settings
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from pytz import timezone as pytz_timezone

from apps.inicio.models import Persona
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import Destino, Documento, DocumentoPDFTokenLectura
from modulos.utiles.clases.correo import CorreoEnviar
from modulos.utiles.clases.ruc import ClaseRUC


class DocumentoConfidencialSolicitarPermiso(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/confidencial/solicitud.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        modo, id = base64.b64decode(request.POST.get("sol-codigo")).decode("ascii").split("-")
        dniult, dnidig = request.POST.get("sol-dni").split("-")
        doc = None
        des = None
        if modo == "DOC":
            doc = Documento.objects.filter(pk=id).first()
        elif modo == "DES":
            des = Destino.objects.filter(pk=id).first()
            if des:
                doc = des.documento
        if doc:
            dnis = doc.ConfidencialDnis(terminaen=dniult)
            if len(dnis) > 0:
                correcto = False
                for dni in dnis:
                    cr = ClaseRUC(dni)
                    if cr.digitoValidador() == dnidig:
                        correcto = dni
                        break
                if correcto:
                    persona = Persona.objects.filter(numero=correcto).first()
                    correo = persona.personaconfiguracion.correoinstitucional
                    if correo:
                        if des:
                            docpdf = des.documentopdf
                        else:
                            docpdf = doc.documentoplantilla.documentopdf_set.first()
                        if docpdf:
                            tokenlectura = docpdf.CreateToken(request, persona)
                            #
                            subject = "%s - Solicitud de Acceso de Documento" % settings.CONFIG_APP["TituloCorto"]
                            subject = ''.join(subject.splitlines())
                            context["tokenlectura"] = tokenlectura
                            body = loader.render_to_string("tramite/documento/confidencial/correo.html", context)
                            ce = CorreoEnviar(tokenlectura.tokencorreo, subject, body)
                            ce.enviar()
                            tokenlectura.tokencorreoenvio = timezone.now()
                            tokenlectura.save()
                            #
                            context["ok"] = "Se le ha enviado un correo con el código de acceso."
                        else:
                            context["error"] = "El documento no tiene contenido."
                    else:
                        context["error"] = "Ud. no tiene correo registrado."
                else:
                    context["error"] = "El último dígito no coincide."
            else:
                context["error"] = "Ud. no tiene acceso a ver este documento."
        else:
            context["error"] = "El documento no existe."
        return self.render_to_response(context=context)


class DocumentoConfidencialAcceder(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/confidencial/acceder.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        modo, id = base64.b64decode(request.POST.get("acc-codigo")).decode("ascii").split("-")
        codigo = request.POST.get("acc-cod")
        doc = None
        des = None
        if modo == "DOC":
            doc = Documento.objects.filter(pk=id).first()
        elif modo == "DES":
            des = Destino.objects.filter(pk=id).first()
            if des:
                doc = des.documento
        if doc:
            fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
            pdftl = DocumentoPDFTokenLectura.objects.filter(
                token=codigo,
                # tokensolicitante=periodoactual,
                tokenusado__isnull=True,
                tokenvalido__gte=fechaActual
            ).first()
            if pdftl:
                request.session["viewconfidential"] = pdftl.pk
                pkwargs = {"pk": doc.pk}
                if des:
                    pkwargs.update({"cod": des.pk})
                context["urldocumentconfidential"] = reverse(
                    viewname="apptra:documento_descargar", kwargs=pkwargs
                )
                context["doc"] = doc
                context["ok"] = "Código correcto."
            else:
                context["error"] = "El código no existe."
        else:
            context["error"] = "El documento no existe."
        return self.render_to_response(context=context)
