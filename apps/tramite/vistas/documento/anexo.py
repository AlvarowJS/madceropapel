"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import json
import os
import shutil
import uuid
from io import BytesIO

import magic
import py7zr
from babel.dates import format_date
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from pytz import timezone as pytz_timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.vistas.varios import listalogos
from apps.sockets.vistas.mensajes import SocketDocFir, SocketMsg
from apps.tramite.formularios.documentodetalle import FormAnexos, FormAnexoFirma
from apps.tramite.models import AnexoFirma, Destino, Anexo, Documento
from modulos.utiles.clases.crud import VistaCreacion


#
#  ANEXO FIRMA - VB - SIMPLE
#

class DocumentoAnexoFirmarVB(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/firmavb/anexofirmarvb.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        if self.request.POST:
            anxfir = AnexoFirma.objects.filter(pk=self.kwargs.get("pk")).first()
            if anxfir:
                anxfir.save(genuuid=True)
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
                        reverse("apptra:documento_anexo_firmarvb_bajar", kwargs={"codigo": anxfir.codigouuid})
                    ),
                    "rutasubida": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_anexo_firmarvb_subir", kwargs={"codigo": anxfir.codigouuid})
                    ),
                    "rutaerror": "%s%s" % (
                        dochost,
                        reverse("apptra:documento_anexo_firmarvb_error", kwargs={"codigo": anxfir.codigouuid})
                    ),
                    "rutalogos": dochost,
                    "logos": listalogos(),
                    "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    "ruc": anxfir.empleado.area.dependencia.rucfirma,
                    "dni": anxfir.empleado.persona.numero,
                    "pagina": 1,
                    "firmamasiva": False,
                    "firmatitularavanzada": False,
                    "esmultiple": False,
                    "esmultipledestino": False,
                    "esanexo": True,
                    "local": "%s - %s - %s" % (
                        anxfir.empleado.area.dependencia.siglas,
                        anxfir.empleado.area.siglas,
                        anxfir.empleado.Cargo()
                    ),
                    "localfull": "%s - %s - %s" % (
                        anxfir.empleado.area.dependencia.nombre,
                        anxfir.empleado.area.nombre,
                        anxfir.empleado.Cargo()
                    ),
                    "modo": "FA" if anxfir.modo == "FI" else "VBA",
                    "razon": "%s en señal de conformidad" % ("Firmo" if anxfir.modo == "FI" else "Viso"),
                    "numerar": False,
                    "stampposxy": False,
                    "firmax": -190,
                    "firmay": 80,
                    "firmaw": 140,
                    "firmah": 34,
                    "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
                }
                pdfJson = json.dumps(pdfJson)
                context["modo"] = anxfir.get_modo_display()
                context["codigo"] = anxfir.codigouuid
                context["anxfirid"] = anxfir.pk
                context["forma"] = "a un anexo"
                docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
                context["urldown"] = "%s%s" % (settings.CONFIG_APP["AppFirma"], docCode)
        return super(DocumentoAnexoFirmarVB, self).render_to_response(context, **response_kwargs)


class DocumentoAnexoFirmarVBBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        anxfir = AnexoFirma.objects.filter(codigouuid=codigo).first()
        if anxfir:
            anxfir.actualizado = timezone.now()
            anxfir.save()
            nombre = anxfir.anexo.archivonombre
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            docpdf = anxfir.anexo.archivofirmado or anxfir.anexo.archivo
            response.write(docpdf)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoAnexoFirmarVBSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        anxfir = AnexoFirma.objects.filter(codigouuid=codigo).first()
        if anxfir:
            anexo = anxfir.anexo
            # Tenemos que verificar si la fecha de actualización del PDF es inferior a la
            # fecha de actualización de la Firma Adicional o VB
            if anexo.actualizado < anxfir.actualizado:
                archivos = request.FILES.getlist("file")
                anexo.archivofirmado = archivos[0].read()
                anexo.actualizado = timezone.now()
                anexo.save()
                anxfir.codigouuid = ""
                anxfir.estado = "FI"
                anxfir.save()
                # Notificamos al cliente
                mensaje = 'El anexo se ha firmado correctamente'
                SocketMsg(
                    userid=anxfir.empleado.persona.usuario.pk,
                    funcpost='refrescarAnexos(%s)' % anexo.documento.pk
                )
                SocketMsg(userid=request.user.id, funcpost='refrescarTableros("dbFirmaVB", true)')
                SocketDocFir("AnxOk", request.user.id, mensaje)
            else:
                mensaje = 'El anexo ha sido alterado'
                SocketDocFir(
                    "AnxError", request.user.id,
                    '%s. Vuelva a realizar la operación de la Firma' % mensaje
                )
        return Response([], status=status.HTTP_200_OK)


class DocumentoAnexoFirmarVBError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        anxfir = AnexoFirma.objects.filter(codigouuid=codigo).first()
        if anxfir:
            # Notificamos al cliente
            SocketDocFir("AnxError", request.user.id, request.POST.get("mensaje"))
        return Response([], status=status.HTTP_200_OK)


class DocumentoAnexoReset(views.APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("pk")
        anx = Anexo.objects.filter(pk=codigo).first()
        if anx:
            anx.archivofirmado = None
            anx.save()
            anx.firmadores.update(estado="SF", estadofecha=None, estadomotivo=None, codigouuid="")
            SocketMsg(
                userid=request.user.pk,
                funcpost='refrescarAnexos(%s)' % anx.documento.pk
            )
        return Response([], status=status.HTTP_200_OK)


class DocumentoDestinoEntFisVista(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/detalles/destino_entfis.html"

    def get_context_data(self, **kwargs):
        context = super(DocumentoDestinoEntFisVista, self).get_context_data(**kwargs)
        context["destino"] = Destino.objects.filter(pk=self.kwargs.get("pk")).first()
        return context


#
#  ANEXO FIRMA - VB - MASIVO
#

class DocumentoAnexoMasivoAgregarVista(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/documento/detalles/anexomasivo.html"
    model = Anexo
    form_class = FormAnexos

    def get_context_data(self, **kwargs):
        context = super(DocumentoAnexoMasivoAgregarVista, self).get_context_data(**kwargs)
        context["formFila"] = FormAnexoFirma()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            documento = Documento.objects.get(pk=self.kwargs.get("pk"))
            firmadores = form.cleaned_data.get("firmadores", "") or "[]"
            firmadores = json.loads(firmadores)
            archivos = self.request.FILES.getlist("archivos")
            for archivo in archivos:
                nombre = archivo.name
                datafile = archivo.read()
                mimetype = magic.from_buffer(datafile, mime=True)
                anexo = Anexo.objects.create(
                    archivonombre=nombre,
                    descripcion=os.path.splitext(nombre)[0],
                    archivo=datafile,
                    documento=documento,
                    creador=self.request.user
                )
                if mimetype == "application/pdf":
                    for firmador in firmadores:
                        formfirmador = FormAnexoFirma(data=firmador)
                        formfirmador.is_valid()
                        formfirmador.instance.anexo = anexo
                        formfirmador.instance.creador = self.request.user
                        formfirmador.save()
            context["anxok"] = True
            context["form"] = form
        return self.render_to_response(context)


class DocumentoAnexoFirmarVBM(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/firmavb/anexofirmarvbm.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        if self.request.POST:
            documento = Documento.objects.filter(pk=self.kwargs.get("pk")).first()
            if documento:
                periodoactual = self.request.user.persona.periodotrabajoactual(
                    self.request.session.get("cambioperiodo")
                )
                anexos = AnexoFirma.objects.filter(
                    empleado=periodoactual,
                    estado="SF",
                    anexo__documento=documento
                )
                if anexos.count() > 0:
                    codigouuid = None
                    empleado = None
                    anexos.update(actualizado=timezone.now())
                    for idx, anxfir in enumerate(anexos):
                        if idx == 0:
                            anxfir.save(genuuid=True)
                            codigouuid = anxfir.codigouuid
                            empleado = anxfir.empleado
                        else:
                            anxfir.codigouuid = codigouuid
                            anxfir.save()
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
                            reverse("apptra:documento_anexo_firmarvbm_bajar", kwargs={"codigo": codigouuid})
                        ),
                        "rutasubida": "%s%s" % (
                            dochost,
                            reverse("apptra:documento_anexo_firmarvbm_subir", kwargs={"codigo": codigouuid})
                        ),
                        "rutaerror": "%s%s" % (
                            dochost,
                            reverse("apptra:documento_anexo_firmarvbm_error", kwargs={"codigo": codigouuid})
                        ),
                        "rutalogos": dochost,
                        "logos": listalogos(),
                        "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                        "ruc": empleado.area.dependencia.rucfirma,
                        "dni": empleado.persona.numero,
                        "pagina": 1,
                        "firmamasiva": True,
                        "firmatitularavanzada": False,
                        "esmultiple": False,
                        "esmultipledestino": False,
                        "esanexo": True,
                        "local": "%s - %s - %s" % (
                            empleado.area.dependencia.siglas,
                            empleado.area.siglas,
                            empleado.Cargo()
                        ),
                        "localfull": "%s - %s - %s" % (
                            empleado.area.dependencia.nombre,
                            empleado.area.nombre,
                            empleado.Cargo()
                        ),
                        "modo": "FAM",
                        "razon": "",
                        "numerar": False,
                        "stampposxy": False,
                        "firmax": 0,
                        "firmay": 0,
                        "firmaw": 0,
                        "firmah": 0,
                        "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
                    }
                    pdfJson = json.dumps(pdfJson)
                    context["modo"] = "Firmando/Visando"
                    context["codigo"] = codigouuid
                    context["forma"] = "varios anexos"
                    docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
                    context["urldown"] = "%s%s" % (settings.CONFIG_APP["AppFirma"], docCode)
                else:
                    context["noanx"] = "No existen anexos para Visar o Firmar"
        return super(DocumentoAnexoFirmarVBM, self).render_to_response(context, **response_kwargs)


class DocumentoAnexoFirmarVBMBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        anxfir = AnexoFirma.objects.filter(codigouuid=codigo)
        if anxfir.count() > 0:
            anxfir.update(actualizado=timezone.now())
            # anexo = anxfir.first().anexo
            # anexo.actualizado = timezone.now()
            # anexo.save()
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
            for anx in anxfir:
                fileNAME = "documento_%s.pdf" % anx.pk
                fileRUTA = "%s/%s" % (tempdir, fileNAME)
                filePDF = open(fileRUTA, "wb")
                filePDF.write(anx.anexo.archivofirmado or anx.anexo.archivo)
                filePDF.close()
                configData.append(
                    {
                        "codigo": anx.pk,
                        "titulo": anx.expedientenro,
                        "firmatitularavanzada": False,
                        "expedientestamp": anx.expedientenro,
                        "numerostamp": anx.anexo.Descripcion(),
                        "fechastamp": "%s, %s" % (
                            str(anx.anexo.documento.documentotipoarea.area.dependencia.ubigeo.Departamento()).title(),
                            format_date(
                                fecha, "dd 'de' MMMM 'de' Y", locale=settings.LANGUAGE_CODE
                            )
                        ),
                        "local": "%s - %s - %s" % (
                            anx.anexo.documento.documentotipoarea.area.dependencia.siglas,
                            anx.anexo.documento.documentotipoarea.area.siglas,
                            anx.anexo.documento.responsable.CargoCorto()
                        ),
                        "localfull": "%s - %s - %s" % (
                            anx.anexo.documento.documentotipoarea.area.dependencia.nombre,
                            anx.anexo.documento.documentotipoarea.area.nombre,
                            anx.anexo.documento.responsable.Cargo()
                        ),
                        "modo": "FIRMA" if anx.modo == "FI" else "VB",
                        "razon": "Soy el Autor" if anx.modo == "FI" else "VB" + (
                            " Por Encargo" if anx.empleado.tipo in ["EP", "EN"] else ""
                        ),
                        "numerar": False,
                        "stampposxy": False,
                        "firmax": 0,
                        "firmay": 0,
                        "firmaw": 0,
                        "firmah": 0
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


class DocumentoAnexoFirmarVBMSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        anxfir = AnexoFirma.objects.filter(codigouuid=codigo)
        if anxfir.count() > 0:
            anexo = anxfir.first().anexo
            # Tenemos que verificar si la fecha de actualización del PDF es inferior a la
            # fecha de actualización de la Firma Adicional o VB
            if anexo.actualizado < anxfir.first().actualizado:
                archivos = request.FILES.getlist("file")
                archivozip = archivos[0].read()
                stream7z = py7zr.SevenZipFile(BytesIO(archivozip), "r")
                _folderTmp = os.path.join(settings.TEMP_DIR, uuid.uuid4().hex)
                stream7z.extractall(path=_folderTmp)
                for _file in stream7z.files:
                    _nombre, _extension = os.path.splitext(_file.filename)
                    _codigoDocumento = int(_nombre.split("_")[1].replace("[AF]", ""))
                    anxfir = AnexoFirma.objects.filter(
                        pk=_codigoDocumento
                    ).first()
                    if anxfir:
                        _fileload = open(os.path.join(_folderTmp, _file.filename), "rb")
                        _fileread = _fileload.read()
                        _fileload.close()
                        anexo = anxfir.anexo
                        anexo.archivofirmado = _fileread
                        anexo.actualizado = timezone.now()
                        anexo.save()
                        anxfir.estado = "FI"
                        anxfir.codigouuid = ""
                        anxfir.save()
                stream7z.close()
                shutil.rmtree(_folderTmp)
                # Notificamos al cliente
                mensaje = 'Los anexos se han firmado correctamente'
                SocketDocFir("AnxMOk", request.user.id, mensaje)
                # SocketMsg(userid=request.user.id, funcpost='refrescarTableros("dbFirmaVB", true)')
                SocketMsg(
                    userid=anxfir.empleado.persona.usuario.pk,
                    funcpost='refrescarAnexos(%s)' % anexo.documento.pk
                )
            else:
                mensaje = 'Los anexos han sido alterados'
                SocketDocFir(
                    "AnxMError", request.user.id,
                    '%s. Vuelva a realizar la operación de la Firma' % mensaje
                )
        return Response([], status=status.HTTP_200_OK)


class DocumentoAnexoFirmarVBMError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        anxfir = AnexoFirma.objects.filter(codigouuid=codigo)
        if anxfir.count() > 0:
            anxfir.update(codigouuid="")
            SocketDocFir("AnxMError", request.user.id, request.POST.get("mensaje"))
        return Response([], status=status.HTTP_200_OK)
