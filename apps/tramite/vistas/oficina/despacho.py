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
from io import BytesIO

import py7zr
from PyPDF2 import PdfFileReader
from babel.dates import format_date
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from pytz import timezone as pytz_timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.vistas.varios import listalogos
from apps.sockets.vistas.mensajes import SocketDocFir, SocketMsg
from apps.tramite.formularios.documentodespacho import FormOficinaDespacho
from apps.tramite.models import Documento
from apps.tramite.tablas.oficinadespacho import TablaOficinaDespacho
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView, BandejaVista


class OficinaBandejaDespacho(BandejaVista):
    template_name = "tramite/oficina/despacho/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["FormOficinaDespacho"] = FormOficinaDespacho(request=request)
        context["TablaOficinaDespacho"] = TablaOficinaDespacho(request=request)
        return self.render_to_response(context=context)


class OficinaBandejaDespachoListar(BandejaListarFeedDataView):
    table = "tablas.oficinadespacho.TablaOficinaDespacho"
    qs = "QueryOficinaBandejaDespacho"

    def get_queryset(self):
        qs = super(OficinaBandejaDespachoListar, self).get_queryset()
        origen = int(self.request.GET.get("origen", "0"))
        if origen > 0:
            qs = qs.filter(responsable__area__id=origen)
        return qs


class OficinaBandejaDespachoFirmaMasiva(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/despacho/firmamasiva.html"

    def get_context_data(self, **kwargs):
        context = super(OficinaBandejaDespachoFirmaMasiva, self).get_context_data(**kwargs)
        ids = eval(self.request.GET.get("ids").replace("_", ","))
        documentos = Documento.objects.filter(pk__in=ids)
        context["documentos"] = documentos
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        context["ids"] = "_".join(
            str(e) for e in list(documentos.filter(responsable=periodoactual).values_list("id", flat=True))
        )
        return context


class OficinaBandejaDespachoFirmaMasivaEjecutar(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/despacho/firmamasivaejecutar.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        codigos = str(self.request.POST.get("codigos"))
        if not codigos.__contains__("_"):
            codigos = "%s_" % codigos
        codigos = eval(codigos.replace("_", ","))
        emitir = self.request.POST.get("emitir", False)
        pdfJson = None
        codigouuid = uuid.uuid4().hex
        token, created = Token.objects.get_or_create(user=self.request.user)
        fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        ncods = 0
        for codigo in codigos:
            doc = Documento.objects.filter(pk=codigo).first()
            if doc.FirmaTitular() and doc.ultimoestado.estado not in ["OF"]:
                ncods += 1
                doc.save(generardoc=True)
                docpdf = doc.des_documento.exclude(ultimoestado__estado="AN").order_by("pk").first().documentopdf
                docplla = docpdf.documentoplantilla
                docplla.codigo = codigouuid
                docplla.save()
                if not pdfJson:
                    dochost = "%s://%s" % (
                        self.request.scheme,
                        self.request.get_host()
                    )
                    pdfJson = {
                        "token": token.key,
                        "rutabajada": "%s%s" % (
                            dochost,
                            reverse("apptra:oficina_bandeja_despacho_firmamasiva_bajar", kwargs={"codigo": codigouuid})
                        ),
                        "rutasubida": "%s%s" % (
                            dochost,
                            reverse("apptra:oficina_bandeja_despacho_firmamasiva_subir", kwargs={
                                "codigo": codigouuid,
                                "emitir": int(emitir)
                            })
                        ),
                        "rutaerror": "%s%s" % (
                            dochost,
                            reverse("apptra:oficina_bandeja_despacho_firmamasiva_error", kwargs={"codigo": codigouuid})
                        ),
                        "rutalogos": dochost,
                        "logos": listalogos(),
                        "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                        "ruc": doc.documentotipoarea.area.dependencia.rucfirma,
                        "dni": doc.responsable.persona.numero,
                        "pagina": 1,
                        "expedientestamp": "",
                        "numerostamp": "",
                        "fechastamp": "",
                        "local": "",
                        "localfull": "",
                        "firmamasiva": True,
                        "firmatitularavanzada": False,
                        "esmultiple": False,
                        "esmultipledestino": False,
                        "modo": "FT",
                        "razon": "Soy el Autor",
                        "numerar": True,
                        "stampposxy": False,
                        "firmax": 0,
                        "firmay": 0,
                        "firmaw": 0,
                        "firmah": 0,
                        "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
                    }
        if ncods > 0:
            pdfJson = json.dumps(pdfJson)
            context["codigo"] = codigouuid
            docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
            context["urldown"] = "%s%s" % (settings.CONFIG_APP["AppFirma"], docCode)
            context["forma"] = "Firmando su{0} documento{0}".format("s" if ncods > 1 else "")
        else:
            context["error"] = "No hay documentos para firmar en esta lista. Verifque el estado de los mismos."
        return super(OficinaBandejaDespachoFirmaMasivaEjecutar, self).render_to_response(context, **response_kwargs)


class OficinaBandejaDespachoFirmaMasivaBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        docs = Documento.objects.filter(documentoplantilla__codigo=codigo)
        if docs.count() > 0:
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
            fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            configData = []
            for doc in docs:
                docpdf = doc.documentoplantilla.documentopdf_set.order_by("pk").first()
                fileNAME = "documento_%s.pdf" % doc.pk
                fileRUTA = "%s/%s" % (tempdir, fileNAME)
                contPDF = docpdf.pdffirma or docpdf.pdf
                filePDF = open(fileRUTA, "wb")
                filePDF.write(contPDF)
                filePDF.close()
                configData.append(
                    {
                        "codigo": doc.pk,
                        "titulo": doc.expedientenro,
                        "expedientestamp": "" if doc.documentotipoarea.documentotipo.plantillaautomatica
                        else doc.expedientenro,
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
                        "numerar": True,
                        "stampposxy": doc.documentotipoarea.documentotipo.plantillaautomatica,
                        "firmax": -182 if doc.documentotipoarea.documentotipo.plantillaautomatica else -217,
                        "firmay": (18 if doc.documentotipoarea.documentotipo.plantillaautomatica else 105) +
                                  doc.documentotipoarea.area.firmamargensuperior,
                        "firmaw": 140,
                        "firmah": 34
                    }
                )
                zipeado.write(fileRUTA, fileNAME)
            # Agregamos las configuraciones de cada archivo a firmar
            fileConfig = "config.txt"
            fileRUTA = "%s/%s" % (tempdir, fileConfig)
            fileDest = open(fileRUTA, "w")
            fileDest.write(json.dumps({"documentos": configData}, ensure_ascii=False))
            fileDest.close()
            zipeado.write(fileRUTA, fileConfig)
            # ======================
            zipeado.close()
            response.write(open(file7z, "rb").read())
            os.remove(file7z)
            shutil.rmtree(tempdir)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class OficinaBandejaDespachoFirmaMasivaSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        emitir = (self.kwargs.get("emitir") == 1)
        from apps.tramite.vistas.documento.emitir import EmitirDocumento
        docs = Documento.objects.filter(documentoplantilla__codigo=codigo)
        if docs.count() > 0:
            archivos = request.FILES.getlist("file")
            archivozip = archivos[0].read()
            stream7z = py7zr.SevenZipFile(BytesIO(archivozip), "r")
            _folderTmp = os.path.join(settings.TEMP_DIR, uuid.uuid4().hex)
            stream7z.extractall(path=_folderTmp)
            for _file in stream7z.files:
                _nombre, _extension = os.path.splitext(_file.filename)
                _codigoDocumento = int(_nombre.split("_")[1])
                docpdf = Documento.objects.filter(
                    pk=_codigoDocumento
                ).first().documentoplantilla.documentopdf_set.first()
                _fileload = open(os.path.join(_folderTmp, _file.filename), "rb")
                _fileread = _fileload.read()
                _fileload.close()
                docpdf.pdffirma = _fileread
                docpdf.estado = "F"
                docpdf.actualizado = timezone.now()
                docpdf.save()
                #
                docpdfstream = io.BytesIO()
                docpdfstream.write(docpdf.pdffirma)
                docpdfR = PdfFileReader(docpdfstream)
                doc = docpdf.documentoplantilla.documento
                doc.folios = docpdfR.getNumPages()
                docpdfstream.close()
                doc.save()
                #
                docest = docpdf.documentoplantilla.documento.ultimoestado
                docest.firmado = True
                docest.save()
                if emitir:
                    EmitirDocumento(docpdf.documentoplantilla.documento, request)
            stream7z.close()
            shutil.rmtree(_folderTmp)
            # Notificamos al cliente
            mensaje = 'Los documentos han sido firmados correctamente'
            SocketDocFir("Ok", request.user.id, mensaje)
            SocketMsg(
                userid=docs.first().creador.pk,
                funcpost='refrescarTableros("dbDespacho", false)'
            )
        return Response([], status=status.HTTP_200_OK)


class OficinaBandejaDespachoFirmaMasivaError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        docs = Documento.objects.filter(documentoplantilla__codigo=codigo)
        if docs.count() > 0:
            #     docplla = doc.documentoplantilla
            #     docplla.codigo = None
            #     docplla.save()
            mensaje = request.POST.get("mensaje")
            # print(mensaje)
            # Notificamos al cliente
            SocketDocFir("Error", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class OficinaBandejaDespachoEmisionMasiva(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/despacho/emisionmasiva.html"
    extra_context = {
        "botonguardartexto": "<i class='fas fa-paper-plane fa-1x'></i> Emitir"
    }

    def get_context_data(self, **kwargs):
        context = super(OficinaBandejaDespachoEmisionMasiva, self).get_context_data(**kwargs)
        if self.request.GET:
            ids = eval(self.request.GET.get("ids").replace("_", ","))
            documentos = Documento.objects.filter(pk__in=ids)
            context["documentos"] = documentos
            periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            ids = ",".join(
                str(e) for e in list(documentos.filter(
                    responsable=periodoactual,
                    ultimoestado__firmado=True
                ).values_list("id", flat=True))
            )
            if not ids:
                context["noBotonGuardar"] = True
            else:
                if not ids.__contains__(","):
                    ids = "%s," % ids
                context["ids"] = ids
        else:
            context["noBotonCancelar"] = True
            context["noBotonGuardar"] = True
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        documentos = eval(request.POST.get("documentos"))
        from apps.tramite.vistas.documento.emitir import EmitirDocumento
        emitidos = False
        for docid in documentos:
            doc = Documento.objects.filter(pk=docid).first()
            if doc.FirmaTitular() == 0 and doc.ultimoestado.estado not in ["OF"]:
                if EmitirDocumento(doc, request):
                    emitidos = True
        if not emitidos:
            context["erroremision"] = "No se puede emitir ningún documento. Revise el motivo en la lista anterior."
            context["ids"] = eval(self.request.POST.get("documentos"))
            context["documentos"] = Documento.objects.filter(pk__in=context["ids"])
        else:
            context["emisionok"] = True
        return self.render_to_response(context=context)
