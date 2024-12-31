"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import io
import json
import os
import shutil
import uuid
from datetime import datetime
from io import BytesIO

import magic
import py7zr
from PyPDF2 import PdfFileWriter, PdfFileReader
from babel.dates import format_date
from django.conf import settings
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, DetailView
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from pytz import timezone as pytz_timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.models import Persona
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.vistas.varios import listalogos
from apps.sockets.vistas.mensajes import SocketDocFir, SocketMsg
from apps.tramite.formularios.documentoemitir import DocumentoEmitirFirmaVBObservarForm
from apps.tramite.models import Documento, DocumentoFirma, DocumentoFirmaEstado, DestinoEstado, DocumentoEstado, \
    Destino, Expediente, DocumentoPDF, DocumentoPDFTokenLectura
from apps.tramite.vistas.documento.emitir import ListaDes, get_lista_anexos, get_lista_referencias
from apps.tramite.vistas.plantillas.destinos import DocumentoDescargarDestVista
from modulos.utiles.clases.crud import VistaEdicion


def GuardarCaducidad(request):
    if request.headers.get("Certfirmante"):
        firmante = request.headers.get("Certfirmante")
        caducidad = datetime.strptime(request.headers.get("Certcaduca"), "%Y-%m-%d-%H:%M:%S")
        persona = Persona.objects.filter(tipodocumentoidentidad__codigo="DNI", numero=firmante).first()
        if persona:
            if hasattr(persona, "personaconfiguracion"):
                pc = persona.personaconfiguracion
                pc.certificadovencimiento = timezone.make_aware(caducidad)
                pc.save()


class DocumentoDescargar(views.APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        cod = self.kwargs.get("cod")
        doc = Documento.objects.filter(pk=pk).first()
        enbase64 = request.headers.get("Base64", "false").lower()
        periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
        if doc:
            if cod:
                destino = Destino.objects.filter(pk=cod).first()
            else:
                docpdf = doc.documentoplantilla.documentopdf_set.first()
                if not docpdf:
                    destino = doc.des_documento.exclude(ultimoestado__estado="AN").order_by("creado").first()
                elif not docpdf.destino:
                    destino = doc.des_documento.exclude(ultimoestado__estado="AN").order_by("creado").first()
                else:
                    destino = docpdf.destino
                if doc.origentipo == "V":
                    if doc.documentotipoarea.documentotipo.esmultiple:
                        for destino in doc.des_documento.exclude(ultimoestado__estado="AN"):
                            if not hasattr(destino, "documentopdf"):
                                DocumentoPDF.objects.create(
                                    pdf=doc.documentoplantilla.contenido,
                                    estado="G",
                                    creador=doc.documentoplantilla.creador,
                                    destino=destino,
                                    documentoplantilla=doc.documentoplantilla
                                )
                    elif not hasattr(destino, "documentopdf"):
                        DocumentoPDF.objects.create(
                            pdf=doc.documentoplantilla.contenido,
                            estado="G",
                            creador=doc.documentoplantilla.creador,
                            destino=destino,
                            documentoplantilla=doc.documentoplantilla
                        )
                else:
                    destino = doc.des_documento.exclude(ultimoestado__estado="AN").filter(
                        Q(periodotrabajo=periodoactual)
                        |
                        Q(periodotrabajo__area=periodoactual.area)
                    ).filter(documentopdf__isnull=False).first()
            if destino:
                if destino.ultimoestado.estado == "NL":
                    DestinoEstado.objects.create(
                        destino=destino,
                        estado="LE",
                        creador=request.user
                    )
                    SocketMsg(
                        userid=request.user.id,
                        funcpost='refrescarTableros("dbEntrada")'
                    )
                    if destino.periodotrabajo and request.user != destino.periodotrabajo.persona.usuario:
                        SocketMsg(
                            userid=destino.periodotrabajo.persona.usuario.pk,
                            funcpost='refrescarTableros("dbEntrada")'
                        )
            nombre = doc.nombreDocumentoPdf()
            lecturaPdfFirmado = None
            filepdf = None
            if doc.origentipo in ["O", "P"]:
                verDoc = False
                if not doc.confidencial:
                    verDoc = True
                elif doc.confidencial:
                    if doc.ultimoestado.estado in ["RE", "PY", "PD", "OF"] and (
                            doc.responsable == periodoactual or doc.creador == request.user
                    ):
                        verDoc = True
                    elif request.session.get("viewconfidential"):
                        pdftl = DocumentoPDFTokenLectura.objects.get(
                            pk=request.session["viewconfidential"]
                        )
                        pdftl.editor = request.user
                        pdftl.tokenusado = timezone.now()
                        pdftl.save()
                        del request.session["viewconfidential"]
                        verDoc = True
                if verDoc:
                    if doc.documentotipoarea.documentotipo.esmultiple and \
                            not doc.documentotipoarea.documentotipo.esmultipledestino and \
                            doc.forma == "I":
                        if not cod:
                            docpdf = doc.documentoplantilla.documentopdf_set.order_by("pk").first()
                        else:
                            docpdf = destino.documentopdf
                        filepdf = docpdf.pdffirma or docpdf.pdf
                        lecturaPdfFirmado = docpdf
                    else:
                        if doc.origentipo in ["F", "V", "X", "C"]:
                            filepdf = doc.documentoplantilla.contenido
                        else:
                            excest = "ANX" if doc.ultimoestado.estado == "AN" else "AN"
                            docpdf = doc.des_documento.exclude(ultimoestado__estado=excest).filter(
                                documentopdf__isnull=False
                            ).first().documentopdf
                            lecturaPdfFirmado = docpdf
                            filepdf = docpdf.pdffirma or docpdf.pdf
            else:
                if doc.documentotipoarea.documentotipo.esmultiple and \
                        not doc.documentotipoarea.documentotipo.esmultipledestino and \
                        doc.forma == "I":
                    if not destino:
                        destino = doc.des_documento.exclude(ultimoestado__estado="AN").order_by("pk").first()
                    if not hasattr(destino, "documentopdf"):
                        DocumentoPDF.objects.create(
                            documentoplantilla=doc.documentoplantilla,
                            destino=destino,
                            pdf=doc.documentoplantilla.contenido,
                            estado="G",
                            creador=request.user
                        )
                    filepdf = destino.documentopdf.pdf
                    if not filepdf:
                        docpdf = destino.documentopdf
                        docpdf.pdf = doc.documentoplantilla.contenido
                        docpdf.save()
                        filepdf = destino.documentopdf.pdf
                    lecturaPdfFirmado = destino.documentopdf
                else:
                    destino = doc.des_documento.exclude(ultimoestado__estado="AN").order_by("pk").first()
                    if not hasattr(destino, "documentopdf"):
                        docpdf = DocumentoPDF.objects.create(
                            documentoplantilla=doc.documentoplantilla,
                            destino=destino,
                            pdf=doc.documentoplantilla.contenido,
                            estado="G",
                            creador=request.user
                        )
                    else:
                        docpdf = destino.documentopdf
                    lecturaPdfFirmado = docpdf
                    filepdf = docpdf.pdf
            if not filepdf and doc.confidencial:
                codigo = "%s-%s" % ("DES" if destino else "DOC", destino.pk if destino else doc.pk)
                codigo = base64.b64encode(codigo.encode("ascii")).decode('ascii')
                context = {
                    "codigo": codigo,
                    "doc": doc,
                    "destino": destino,
                    "token": request.META.get("CSRF_COOKIE")
                }
                tplpermiso = render_to_string("tramite/documento/confidencial/permiso.html", context)
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='text/html'
                )
                response.write(tplpermiso)
            else:
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/pdf'
                )
                #
                if doc.ultimoestado.estado == "AN":
                    docpdfstream = io.BytesIO()
                    docpdfstream.write(filepdf)
                    pdf_origen = PdfFileReader(docpdfstream)
                    output = PdfFileWriter()
                    for pagina in pdf_origen.pages:
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=A4)
                        text = "ANULADO"
                        # text_width = can.stringWidth(text, "Helvetica", 80)
                        can.setFont("Helvetica", 110)
                        can.saveState()
                        can.rotate(45)
                        can.setStrokeColorRGB(255, 0, 0, 0.3)
                        can.setFillColorRGB(255, 0, 0, 0.2)
                        can.translate(canvas.pdfdoc.PDFPage.pagewidth / 2.2, 80 / 1.2)
                        can.drawString(0, 0, text, 2, 3, 60)
                        can.restoreState()
                        can.save()
                        packet.seek(0)
                        pdf_watermark = PdfFileReader(packet)
                        # page = pdf_origen.getPage(0)
                        pagina.mergePage(pdf_watermark.getPage(0))
                        output.addPage(pagina)
                    docpdfstream = io.BytesIO()
                    output.write(docpdfstream)
                    filepdf = docpdfstream.getvalue()
                #
                response["Content-Disposition"] = "attachment; filename=%s" % nombre
                if enbase64 == "true":
                    response.write(base64.b64encode(filepdf).decode('utf-8'))
                else:
                    response.write(filepdf)
                if lecturaPdfFirmado:
                    lecturaPdfFirmado.CrearRevision(request)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoDescargarFast(views.APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        des = Destino.objects.filter(pk=pk).first()
        if des and not des.documento.confidencial:
            if des.documento.documentotipoarea.documentotipo.esmultiple and \
                    not des.documento.documentotipoarea.documentotipo.esmultipledestino and \
                    des.documento.forma == "I":
                # docpdf = des.documento.documentoplantilla.documentopdf_set.first()
                docpdf = des.documentopdf
                nomfile = docpdf.nombreDoc()
                docpdf.CrearRevision(request)
                docpdf = docpdf.pdffirma or docpdf.pdf
                nomfile = "%s.pdf" % nomfile
            else:
                docpdf = des.documento.documentoplantilla.documentopdf_set.first()
                docpdf.CrearRevision(request)
                docpdf = docpdf.pdffirma or docpdf.pdf
                nomfile = des.documento.nombreDocumentoPdf()
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type=magic.from_buffer(docpdf, mime=True)
            )
            response["Content-Disposition"] = "attachment; filename=%s" % nomfile
            response.write(docpdf)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoDescargarFull(views.APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        doc = Documento.objects.filter(pk=pk).first()
        if doc:
            if doc.confidencial:
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type="text/html"
                )
                # response.write(docfile)
                return response
            else:
                if doc.documentotipoarea.documentotipo.esmultiple and \
                        not doc.documentotipoarea.documentotipo.esmultipledestino and \
                        doc.forma == "I":
                    # Comprimimos todos los documentos y creamos su revisión
                    nomfile = "%s.7z" % doc.nombreDoc()
                    tempdir = os.path.join("%s/%s" % (settings.TEMP_DIR, uuid.uuid4().hex))
                    os.mkdir(tempdir)
                    file7z = os.path.join("%s/%s.7z" % (tempdir, uuid.uuid4().hex))
                    zipeado = py7zr.SevenZipFile(file7z, "w")
                    for idx, docpdf in enumerate(doc.documentoplantilla.documentopdf_set.order_by("pk")):
                        fileNAME = "%s" % docpdf.nombreDoc()
                        fileNAME = "%s.pdf" % fileNAME
                        fileRUTA = "%s/%s" % (tempdir, fileNAME)
                        docpdf.CrearRevision(request)
                        contPDF = docpdf.pdffirma or docpdf.pdf
                        filePDF = open(fileRUTA, "wb")
                        filePDF.write(contPDF)
                        filePDF.close()
                        zipeado.write(fileRUTA, fileNAME)
                        os.remove(fileRUTA)
                    zipeado.close()
                    docfile = open(file7z, "rb").read()
                    shutil.rmtree(tempdir)
                    content_type = "application/x-7z-compressed"
                else:
                    docpdf = doc.documentoplantilla.documentopdf_set.first()
                    if not docpdf:
                        docpdf = DocumentoPDF.objects.create(
                            documentoplantilla=doc.documentoplantilla,
                            destino=doc.des_documento.exclude(ultimoestado__estado="AN").order_by("pk").first(),
                            pdf=doc.documentoplantilla.contenido,
                            estado="G",
                            creador=request.user
                        )
                    docpdf.CrearRevision(request)
                    docfile = docpdf.pdffirma or docpdf.pdf
                    content_type = "application/pdf"
                    nomfile = doc.nombreDocumentoPdf()
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type=content_type
                )
                response["Content-Disposition"] = "attachment; filename=%s" % nomfile
                response.write(docfile)
                return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoDescargarDest(views.APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        doc = Documento.objects.filter(pk=pk).first()
        if doc:
            if doc.documentotipoarea.documentotipo.esmultiple and \
                    not doc.documentotipoarea.documentotipo.esmultipledestino and \
                    doc.forma == "I":
                nomfile = doc.nombreDocumentoPdf()
                #
                eav = DocumentoDescargarDestVista(*args, **kwargs)
                eav.kwargs = self.kwargs
                eav.request = self.request
                context = self.get_renderer_context()
                context["configapp"] = settings.CONFIG_APP
                #
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type="application/pdf"
                )
                response["Content-Disposition"] = "attachment; filename=%s" % nomfile
                response.write(eav.render_to_response(context=context).getvalue())
                return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


def ObtenerDestinosReferencias(destinos):
    _result = destinos
    for destino in Destino.objects.filter(pk__in=destinos):
        referencias = list(destino.documento.referencias.values_list("destino_id", flat=True))
        if len(referencias) > 0:
            _result += ObtenerDestinosReferencias(referencias)
    return _result


class DocumentoDescargar2(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/visualizar.html"

    def render_to_response(self, context, **response_kwargs):
        ori = self.kwargs.get("ori")
        cod = self.kwargs.get("cod")
        expediente = None
        destinos = None
        if ori == "documento":
            documento = Documento.objects.filter(pk=cod).first()
            if documento.expediente:
                expediente = Expediente.objects.get(pk=documento.expediente.pk)
            context["documento"] = documento
            destinos = list(documento.referencias.values_list("destino_id", flat=True))
            ObtenerDestinosReferencias(destinos)
        elif ori == "destino":
            expediente = Expediente.objects.get(pk=Destino.objects.get(pk=cod).documento.expediente.pk)
            destinos = [cod]
            ObtenerDestinosReferencias(destinos)
        elif ori == "documentofirma":
            documento = DocumentoFirma.objects.get(pk=cod).documento
            if documento.expediente:
                expediente = Expediente.objects.get(
                    pk=documento.expediente.pk
                )
            destinos = list(documento.des_documento.exclude(ultimoestado__estado="AN").values_list("pk", flat=True))
            ObtenerDestinosReferencias(destinos)
        else:
            print("aqui", ori)
        if destinos:
            destinos = Destino.objects.filter(
                pk__in=destinos
            )
            if expediente:
                destinos = destinos.annotate(
                    exporden=Case(
                        When(
                            documento__expediente__anio=expediente.anio,
                            documento__expediente__numero=expediente.numero,
                            then=Value(0)
                        ),
                        default=Value(1),
                        output_field=IntegerField()
                    )
                )
            else:
                destinos = destinos.annotate(orden=Value(0))
            destinos = destinos.order_by(
                "exporden", "documento__expediente__anio", "documento__expediente__numero", "-pk"
            )
            context["expediente"] = expediente
            context["expedientes"] = destinos.aggregate(expedientes=Count(
                "documento__expediente__numero", distinct=True
            ))["expedientes"]
            context["destinos"] = destinos
        return super(DocumentoDescargar2, self).render_to_response(context, **response_kwargs)


class DocumentoAnexos(TemplateValidaLogin, DetailView):
    template_name = "tramite/documento/anexos.html"
    model = Documento
    context_object_name = "oDoc"

    def get_context_data(self, **kwargs):
        context = super(DocumentoAnexos, self).get_context_data(**kwargs)
        context["visual"] = True
        context["anexos"] = json.dumps(get_lista_anexos(self.get_object(), self.request, False), ensure_ascii=False)
        return context


class DocumentoReferencias(TemplateValidaLogin, DetailView):
    template_name = "tramite/documento/referencias.html"
    model = Documento
    context_object_name = "oDoc"

    def get_context_data(self, **kwargs):
        context = super(DocumentoReferencias, self).get_context_data(**kwargs)
        context["visual"] = True
        context["referencias"] = json.dumps(get_lista_referencias(self.get_object()), ensure_ascii=False)
        return context


class DocumentoEmitirFirmar(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/emitir/emitir_firmar_pdf.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        if self.request.POST:
            doc = Documento.objects.filter(pk=self.kwargs.get("pk")).first()
            if doc:
                doc.save(generardoc=True)
                doc = Documento.objects.filter(pk=self.kwargs.get("pk")).first()
                dochost = "%s://%s" % (
                    self.request.scheme,
                    self.request.get_host()
                )
                docpdf = doc.des_documento.exclude(ultimoestado__estado="AN").filter(
                    documentopdf__isnull=False
                ).first().documentopdf
                docplla = docpdf.documentoplantilla
                docplla.save(genuuid=True)
                token, created = Token.objects.get_or_create(user=self.request.user)
                fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
                pdfJson = {
                    "token": token.key,
                    "rutabajada": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_emitir_firmar_bajar", kwargs={"codigo": docplla.codigo})
                    ),
                    "rutasubida": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_emitir_firmar_subir", kwargs={"codigo": docplla.codigo})
                    ),
                    "rutaerror": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_emitir_firmar_error", kwargs={"codigo": docplla.codigo})
                    ),
                    "rutalogos": dochost,
                    "logos": listalogos(),
                    "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    "ruc": doc.documentotipoarea.area.dependencia.rucfirma,
                    "dni": self.request.user.persona.numero if
                    self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).tipo
                    in ["EP", "EN"] else doc.responsable.persona.numero,
                    "pagina": 1,
                    "expedientestamp": "" if doc.documentotipoarea.documentotipo.plantillaautomatica else
                    doc.expedientenro,
                    "numerostamp": doc.obtenerNumeroSiglas(),
                    "fechastamp": "%s, %s" % (
                        str(doc.documentotipoarea.area.dependencia.ubigeo.Departamento()).title(),
                        format_date(
                            fecha, "dd 'de' MMMM 'de' Y", locale=settings.LANGUAGE_CODE
                        )
                    ),
                    "local": "%s - %s - %s" % (
                        doc.documentotipoarea.area.dependencia.siglas,
                        doc.documentotipoarea.area.siglas,
                        doc.responsable.CargoCorto()
                    ),
                    "localfull": "%s - %s - %s" % (
                        doc.documentotipoarea.area.dependencia.nombre,
                        doc.documentotipoarea.area.nombre,
                        doc.responsable.Cargo()
                    ),
                    "firmamasiva": False,
                    "firmatitularavanzada": doc.documentotipoarea.documentotipo.correlativounico,
                    "esmultiple": doc.documentotipoarea.documentotipo.esmultiple and doc.forma == "I",
                    "esmultipledestino": doc.documentotipoarea.documentotipo.esmultipledestino,
                    "modo": "FE" if doc.responsable.tipo == "EN" else "FT",
                    "razon": "Por Encargo" if doc.responsable.tipo in ["EP", "EN"] else
                    "Soy el autor del documento",
                    "numerar": True,  # not doc.documentotipoarea.documentotipo.plantillaautomatica,
                    "stampposxy": doc.documentotipoarea.documentotipo.plantillaautomatica,
                    "firmax": -182 if doc.documentotipoarea.documentotipo.plantillaautomatica else -217,
                    "firmay": (18 if doc.documentotipoarea.documentotipo.plantillaautomatica else 105) +
                              doc.documentotipoarea.area.firmamargensuperior,
                    "firmaw": 140,
                    "firmah": 34,
                    "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
                }
                pdfJson = json.dumps(pdfJson)
                context["codigo"] = docplla.codigo
                docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
                context["urldown"] = "%s%s" % (
                    settings.CONFIG_APP["AppFirma"],
                    docCode
                )
                context["iddoc"] = doc.pk
                context["forma"] = \
                    "Firmando " + \
                    ("sus documentos" if doc.documentotipoarea.documentotipo.esmultiple and
                                         not doc.documentotipoarea.documentotipo.esmultipledestino and
                                         doc.forma == "I"
                     else "su documento")
        return super(DocumentoEmitirFirmar, self).render_to_response(context, **response_kwargs)


class DocumentoEmitirFirmarBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        doc = Documento.objects.filter(documentoplantilla__codigo=codigo).first()
        if doc:
            nombre = doc.nombreDocumentoPdf()
            if doc.documentotipoarea.documentotipo.esmultiple and \
                    not doc.documentotipoarea.documentotipo.esmultipledestino and \
                    doc.forma == "I":
                # Comprimimos todos los PDFs para enviarlos al Cliente
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/x-7z-compressed'
                )
                nombre = "%s.7z" % uuid.uuid4().hex
                response["Content-Disposition"] = "attachment; filename=%s" % nombre
                tempdir = os.path.join("%s/%s" % (settings.TEMP_DIR, uuid.uuid4().hex))
                os.mkdir(tempdir)
                file7z = os.path.join("%s/%s.7z" % (tempdir, uuid.uuid4().hex))
                zipeado = py7zr.SevenZipFile(file7z, "w")
                for docpdf in doc.documentoplantilla.documentopdf_set.order_by("pk"):
                    fileNAME = "documento_%s.pdf" % docpdf.destino.pk
                    fileRUTA = "%s/%s" % (tempdir, fileNAME)
                    contPDF = docpdf.pdffirma or docpdf.pdf
                    filePDF = open(fileRUTA, "wb")
                    filePDF.write(contPDF)
                    filePDF.close()
                    zipeado.write(fileRUTA, fileNAME)
                    os.remove(fileRUTA)
                # Agregamos los destinos
                fileNAME = "destinos.txt"
                fileRUTA = "%s/%s" % (tempdir, fileNAME)
                fileDest = open(fileRUTA, "w")
                fileDest.write(json.dumps({"destinos": ListaDes(doc)}, ensure_ascii=False))
                fileDest.close()
                zipeado.write(fileRUTA, fileNAME)
                # ======================
                zipeado.close()
                response.write(open(file7z, "rb").read())
                os.remove(file7z)
                shutil.rmtree(tempdir)
            else:
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/pdf'
                )
                response["Content-Disposition"] = "attachment; filename=%s" % nombre
                if doc.documentotipoarea.documentotipo.esmultiple and \
                        not doc.documentotipoarea.documentotipo.esmultipledestino and \
                        doc.forma == "I":
                    response.write(doc.contenido)
                else:
                    docpdf = doc.des_documento.exclude(ultimoestado__estado="AN").filter(
                        documentopdf__isnull=False
                    ).first().documentopdf
                    response.write(docpdf.pdffirma or docpdf.pdf)
                    response.flush()
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoEmitirFirmarSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        doc = Documento.objects.filter(documentoplantilla__codigo=codigo).first()
        if doc:
            doc.folios = None
            docest = doc.ultimoestado
            if docest.estado == "PD":
                docest.firmado = True
                docest.save()
                GuardarCaducidad(request)
                archivos = request.FILES.getlist("file")
                if doc.documentotipoarea.documentotipo.esmultiple and \
                        not doc.documentotipoarea.documentotipo.esmultipledestino and \
                        doc.forma == "I":
                    # Descomprimimos y guardamos los archivos en la BD
                    archivozip = archivos[0].read()
                    stream7z = py7zr.SevenZipFile(BytesIO(archivozip), "r")
                    _folderTmp = os.path.join(settings.TEMP_DIR, uuid.uuid4().hex)
                    stream7z.extractall(path=_folderTmp)
                    for _file in stream7z.files:
                        _nombre, _extension = os.path.splitext(_file.filename)
                        _codigoDestino = int(_nombre.split("_")[1])
                        documentopdf = doc.des_documento.filter(pk=_codigoDestino).first().documentopdf
                        _fileload = open(os.path.join(_folderTmp, _file.filename), "rb")
                        _fileread = _fileload.read()
                        _fileload.close()
                        documentopdf.pdffirma = _fileread
                        documentopdf.estado = "F"
                        documentopdf.actualizado = timezone.now()
                        documentopdf.save()
                        if not doc.folios:
                            docpdfstream = io.BytesIO()
                            docpdfstream.write(_fileread)
                            docpdfR = PdfFileReader(docpdfstream)
                            doc.folios = docpdfR.getNumPages()
                            docpdfstream.close()
                    stream7z.close()
                    shutil.rmtree(_folderTmp)
                else:
                    docpdf = doc.des_documento.exclude(ultimoestado__estado="AN").filter(
                        documentopdf__isnull=False
                    ).first().documentopdf
                    docpdf.pdffirma = archivos[0].read()
                    docpdf.estado = "F"
                    docpdf.save()
                    docpdfstream = io.BytesIO()
                    docpdfstream.write(docpdf.pdffirma)
                    docpdfR = PdfFileReader(docpdfstream)
                    doc.folios = docpdfR.getNumPages()
                    docpdfstream.close()
                doc.save()
                docplla = doc.documentoplantilla
                docplla.codigo = None
                docplla.save()
                # Notificamos al cliente
                mensaje = 'El documento se ha firmado correctamente'
                if doc.documentotipoarea.documentotipo.esmultiple and \
                        not doc.documentotipoarea.documentotipo.esmultipledestino and \
                        doc.forma == "I":
                    mensaje = 'Los documentos han sido firmados correctamente'
                SocketDocFir("Ok", request.user.id, mensaje)
                SocketMsg(
                    userid=doc.creador.pk,
                    funcpost='refrescarTableros("dbDespacho", false)'
                )
            else:
                SocketDocFir("Error", request.user.id, "El documento está en estado %s" % docest.get_estado_display())
        else:
            SocketDocFir("Error", request.user.id, "El documento ya no existe")
        return Response([], status=status.HTTP_200_OK)


class DocumentoEmitirFirmarError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        doc = Documento.objects.filter(documentoplantilla__codigo=codigo).first()
        if doc:
            docplla = doc.documentoplantilla
            docplla.codigo = None
            docplla.save()
            mensaje = request.POST.get("mensaje")
            # Notificamos al cliente
            SocketDocFir("Error", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class DocumentoEmitirFirmarVB(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/emitir/emitir_firmarvb_pdf.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        if self.request.POST:
            docfir = DocumentoFirma.objects.filter(pk=self.kwargs.get("pk")).first()
            if docfir:
                docfir.save(genuuid=True)
                dochost = "%s://%s" % (
                    self.request.scheme,
                    self.request.get_host()
                )
                token, created = Token.objects.get_or_create(user=self.request.user)
                fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
                pdfJson = {
                    "token": token.key,
                    "rutabajada": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_emitir_firmarvb_bajar", kwargs={"codigo": docfir.codigouuid})
                    ),
                    "rutasubida": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_emitir_firmarvb_subir", kwargs={"codigo": docfir.codigouuid})
                    ),
                    "rutaerror": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_emitir_firmarvb_error", kwargs={"codigo": docfir.codigouuid})
                    ),
                    "rutalogos": dochost,
                    "logos": listalogos(),
                    "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    "ruc": docfir.empleado.area.dependencia.rucfirma,
                    "dni": docfir.empleado.persona.numero,
                    "pagina": 1,
                    "firmamasiva": False,
                    "firmatitularavanzada": False,
                    "esmultiple": docfir.documento.documentotipoarea.documentotipo.esmultiple and
                                  docfir.documento.forma == "I",
                    "esmultipledestino": docfir.documento.documentotipoarea.documentotipo.esmultipledestino,
                    "local": "%s - %s - %s" % (
                        docfir.empleado.area.dependencia.siglas,
                        docfir.empleado.area.siglas,
                        docfir.empleado.CargoCorto()
                    ),
                    "localfull": "%s - %s - %s" % (
                        docfir.empleado.area.dependencia.nombre,
                        docfir.empleado.area.nombre,
                        docfir.empleado.Cargo()
                    ),
                    "modo": ("FA" if docfir.modo == "FI" else "VBA") if
                    docfir.documento.documentotipoarea.documentotipo.correlativounico else
                    ("FD" if docfir.modo == "FI" else "VB"),
                    "razon": "Soy el Autor" if docfir.modo == "FI" else "Doy V°B°" + (
                        " Por Encargo" if docfir.empleado.tipo in ["EP", "EN"] else ""
                    ),
                    "numerar": False,
                    "stampposxy": False,
                    "firmax": -190,
                    "firmay": 80,
                    "firmaw": 140,
                    "firmah": 34,
                    "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
                }
                pdfJson = json.dumps(pdfJson)
                context["modo"] = docfir.get_modo_display()
                context["codigo"] = docfir.codigouuid
                context["docid"] = docfir.documento.pk
                context["docfirid"] = docfir.pk
                context["forma"] = (
                    "a los documentos" if docfir.documento.documentotipoarea.documentotipo.esmultiple
                                          and not docfir.documento.documentotipoarea.documentotipo.esmultipledestino
                                          and docfir.documento.forma == "I"
                    else "al documento"
                )
                docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
                context["urldown"] = "%s%s" % (settings.CONFIG_APP["AppFirma"], docCode)
        return super(DocumentoEmitirFirmarVB, self).render_to_response(context, **response_kwargs)


class DocumentoEmitirFirmarVBBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        docfir = DocumentoFirma.objects.filter(codigouuid=codigo).first()
        if docfir:
            docfir.actualizado = timezone.now()
            docfir.save()
            nombre = docfir.documento.nombreDocumentoPdf()
            if docfir.documento.documentotipoarea.documentotipo.esmultiple and \
                    not docfir.documento.documentotipoarea.documentotipo.esmultipledestino and \
                    docfir.documento.forma == "I":
                # Comprimimos todos los PDFs para enviarlos al Cliente
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/x-7z-compressed'
                )
                nombre = "%s.7z" % uuid.uuid4().hex
                response["Content-Disposition"] = "attachment; filename=%s" % nombre
                tempdir = os.path.join("%s/%s" % (settings.TEMP_DIR, uuid.uuid4().hex))
                os.mkdir(tempdir)
                file7z = os.path.join("%s/%s.7z" % (tempdir, uuid.uuid4().hex))
                zipeado = py7zr.SevenZipFile(file7z, "w")
                for docpdf in docfir.documento.documentoplantilla.documentopdf_set.order_by("pk"):
                    fileNAME = "documento_%s.pdf" % docpdf.destino.pk
                    fileRUTA = "%s/%s" % (tempdir, fileNAME)
                    contPDF = docpdf.pdffirma or docpdf.pdf
                    filePDF = open(fileRUTA, "wb")
                    filePDF.write(contPDF)
                    filePDF.close()
                    zipeado.write(fileRUTA, fileNAME)
                    os.remove(fileRUTA)
                # Agregamos los destinos
                fileNAME = "destinos.txt"
                fileRUTA = "%s/%s" % (tempdir, fileNAME)
                fileDest = open(fileRUTA, "w")
                fileDest.write(json.dumps({"destinos": ListaDes(docfir.documento)}, ensure_ascii=False))
                fileDest.close()
                zipeado.write(fileRUTA, fileNAME)
                # ======================
                zipeado.close()
                response.write(open(file7z, "rb").read())
                os.remove(file7z)
                shutil.rmtree(tempdir)
            else:
                response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/pdf'
                )
                response["Content-Disposition"] = "attachment; filename=%s" % nombre
                documentpdf = docfir.documento.des_documento.exclude(ultimoestado__estado="AN").filter(
                    documentopdf__isnull=False
                ).first().documentopdf
                docpdf = documentpdf.pdffirma or documentpdf.pdf
                response.write(docpdf)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoEmitirFirmarVBSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        docfir = DocumentoFirma.objects.filter(codigouuid=codigo).first()
        if docfir:
            documentopdf = docfir.documento.des_documento.exclude(ultimoestado__estado="AN").filter(
                documentopdf__isnull=False
            ).first().documentopdf
            # Tenemos que verificar si la fecha de actualización del PDF es inferior a la
            # fecha de actualización de la Firma Adicional o VB
            GuardarCaducidad(request)
            if documentopdf.actualizado < docfir.actualizado:
                archivos = request.FILES.getlist("file")
                if docfir.documento.documentotipoarea.documentotipo.esmultiple and \
                        not docfir.documento.documentotipoarea.documentotipo.esmultipledestino and \
                        docfir.documento.forma == "I":
                    # Descomprimimos y guardamos los archivos en la BD
                    archivozip = archivos[0].read()
                    stream7z = py7zr.SevenZipFile(BytesIO(archivozip), "r")
                    _folderTmp = os.path.join(settings.TEMP_DIR, uuid.uuid4().hex)
                    stream7z.extractall(path=_folderTmp)
                    for _file in stream7z.files:
                        _nombre, _extension = os.path.splitext(_file.filename)
                        _codigoDestino = int(_nombre.split("_")[1])
                        documentopdf = docfir.documento.des_documento.filter(pk=_codigoDestino).first().documentopdf
                        _fileload = open(os.path.join(_folderTmp, _file.filename), "rb")
                        _fileread = _fileload.read()
                        _fileload.close()
                        documentopdf.pdffirma = _fileread
                        documentopdf.estado = "V"
                        documentopdf.actualizado = timezone.now()
                        documentopdf.save()
                    stream7z.close()
                    shutil.rmtree(_folderTmp)
                else:
                    documentopdf.pdffirma = archivos[0].read()
                    documentopdf.estado = "V"
                    documentopdf.actualizado = timezone.now()
                    documentopdf.save()
                docfir.estado = DocumentoFirmaEstado.objects.get(codigo="FI")
                docfir.codigouuid = None
                docfir.save()
                # Notificamos al cliente
                mensaje = 'El documento se ha firmado correctamente'
                if docfir.documento.documentotipoarea.documentotipo.esmultiple and \
                        not docfir.documento.documentotipoarea.documentotipo.esmultipledestino and \
                        docfir.documento.forma == "I":
                    mensaje = 'Los documentos han sido firmados correctamente'
                SocketDocFir("VBOk", request.user.id, mensaje)
                SocketMsg(
                    userid=docfir.documento.responsable.persona.usuario.pk,
                    funcpost='refrescarTableros("dbDespacho", false)'
                )
            else:
                mensaje = 'El documento ha sido alterado'
                if docfir.documento.documentotipoarea.documentotipo.esmultiple and \
                        not docfir.documento.documentotipoarea.documentotipo.esmultipledestino and \
                        docfir.documento.forma == "I":
                    mensaje = 'Los documentos han sido alterados'
                SocketDocFir(
                    "VBError", request.user.id,
                    '%s. Vuelva a realizar la operación de la Firma' % mensaje
                )
        return Response([], status=status.HTTP_200_OK)


class DocumentoEmitirFirmarVBError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        docfir = DocumentoFirma.objects.filter(codigouuid=codigo).first()
        if docfir:
            # Notificamos al cliente
            SocketDocFir("VBError", request.user.id, request.POST.get("mensaje"))
        return Response([], status=status.HTTP_200_OK)


class DocumentoEmitirFirmarVBObservar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/emitir/emitir_firmarvb_observar.html"
    model = Documento
    form_class = DocumentoEmitirFirmaVBObservarForm
    extra_context = {
        'botonguardartexto': 'Observar'
    }

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        if form.is_valid():
            #
            doc = self.object
            firmador = doc.firmas.filter(
                empleado=self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            ).first()
            firmador.motivorechazado = form.cleaned_data["observacion"]
            firmador.estado = DocumentoFirmaEstado.objects.get(codigo="RE")
            firmador.actualizado = timezone.now()
            firmador.editor = self.request.user
            firmador.save()
            #
            DocumentoEstado.objects.create(
                documento=doc,
                estado="OF",
                creador=self.request.user
            )
            #
            SocketMsg(
                tipo='error',
                clase='bg-danger',
                userid=doc.creador.id,
                titulo='Documento Observado',
                mensaje='Hola %s, han realizado una observación a su documento' % doc.creador.persona.nombres,
                funcpost='refrescarTableros("dbDespacho", false)'
            )
            for firmador in doc.firmas.all():
                SocketMsg(
                    userid=firmador.empleado.persona.usuario.pk,
                    funcpost='refrescarTableros("dbFirmaVB", true)'
                )
            context["observacion_correcta"] = True
        return self.render_to_response(context)
