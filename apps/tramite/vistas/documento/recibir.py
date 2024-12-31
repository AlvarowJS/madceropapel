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

import py7zr
from PIL import Image
from babel.dates import format_date
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.authtoken.models import Token
from pytz import timezone as pytz_timezone
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import pyqrcodeng as pyqrcode

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import PeriodoTrabajo
from apps.organizacion.vistas.varios import listalogos
from apps.sockets.vistas.mensajes import SocketMsg, SocketDocFir
from apps.tramite.formularios.documentorecibir import DestinoRecibirForm
from apps.tramite.models import Destino, DestinoEstado
from apps.tramite.vistas.plantillas.recepcionfisica import DocumentoRecibirFisicoVista
from modulos.utiles.clases.crud import VistaEdicion
from modulos.utiles.clases.varios import randomString


class DocumentoRecibir(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/recibir/recibir_estado.html"
    model = Destino
    form_class = DestinoRecibirForm

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.documento.ultimoestado.estado in ["EM", "RP", "RT", "AT", "AR"]:
                ultimoestado = DestinoEstado(
                    destino=destino,
                    estado="RE",
                    creador=self.request.user
                )
                ultimoestado.save()
                SocketMsg(
                    tipo="info",
                    clase="bg-dark",
                    userid=self.request.user.pk,
                    titulo="Bandeja Recepcionados",
                    mensaje="Se recibió el documento correctamente",
                    funcpost='refrescarTableros("dbEntrada,dbRecepcionados", true)'
                )
                context["urledit"] = reverse("apptra:documento_emitir_editar", kwargs={
                    "pk": destino.documento.id,
                    "tab": "dbEntrada",
                    "tabid": destino.id
                })
                context["ok"] = "El documento ha sido recibido correctamente"
            else:
                context["error"] = "El documento no puede ser recepcionado; porque ha cambiado su estado y ahora " \
                                   "se encuentra <span class='font-weight-bolder text-primary'>%s</span>."
                context["error"] = context["error"] % (
                    destino.documento.ultimoestado.get_estado_display()
                )
        return self.render_to_response(context)


class DocumentoRecibirAnular(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/recibir/recibir_estado.html"
    model = Destino
    form_class = DestinoRecibirForm

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.entregafisica:
                destino.entregafisicacargo = None
                destino.entregafisicafecha = None
                destino.entregafisicareceptor = None
                destino.save()
            if destino.ultimoestado.estado != "NL":
                ultimoestado = DestinoEstado(
                    destino=destino,
                    estado="NL",
                    creador=self.request.user
                )
                ultimoestado.save()
            # Notificamos al que Recepcionó
            SocketMsg(
                userid=destino.periodotrabajo.persona.usuario.pk,
                funcpost='refrescarTableros("dbEntrada,dbRecepcionados", true)'
            )
            if destino.periodotrabajo.persona.usuario != self.request.user:
                SocketMsg(
                    userid=self.request.user.pk,
                    funcpost='refrescar_tabladbRecepcionadosO();refrescar_tabladbRecepcionadosP();'
                )
        return self.render_to_response(context)


# Recibir un documento con cargo Físico
class DocumentoRecibirFisico(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/recibir/recibir_fisico.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        destino = Destino.objects.filter(pk=self.kwargs.get("pk")).first()
        if destino:
            #
            dochost = "%s://%s" % (
                self.request.scheme,
                self.request.get_host()
            )
            token, created = Token.objects.get_or_create(user=self.request.user)
            fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            responsable = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            dependencia = responsable.area.dependencia
            #
            pdfJson = {
                "token": token.key,
                "rutabajada": "%s%s" % (
                    dochost,
                    reverse("apptra:documento_recibirf_b", kwargs={"pk": destino.pk, "ptid": responsable.pk})
                ),
                "rutasubida": "%s%s" % (
                    dochost,
                    reverse("apptra:documento_recibirf_s", kwargs={"pk": destino.pk})
                ),
                "rutaerror": "%s%s" % (
                    dochost,
                    reverse("apptra:documento_recibirf_e", kwargs={"pk": destino.pk})
                ),
                "rutalogos": dochost,
                "logos": listalogos(),
                "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "ruc": dependencia.rucfirma,
                "dni": responsable.persona.numero,
                "pagina": 1,
                "expedientestamp": "",
                "numerostamp": "CARGO DE ENTREGA FÍSICA",
                "fechastamp": "%s, %s" % (
                    str(dependencia.ubigeo.Departamento()).title(),
                    format_date(
                        fecha, "dd 'de' MMMM 'de' Y", locale=settings.LANGUAGE_CODE
                    )
                ),
                "local": "%s - %s - %s" % (
                    dependencia.siglas,
                    responsable.area.siglas,
                    responsable.CargoCorto()
                ),
                "localfull": "%s - %s - %s" % (
                    dependencia.nombre,
                    responsable.area.nombre,
                    responsable.Cargo()
                ),
                "firmamasiva": False,
                "firmatitularavanzada": False,
                "esmultiple": False,
                "esmultipledestino": False,
                "modo": "FR",
                "razon": "Cargo de Recepción",
                "numerar": False,
                "stampposxy": True,
                "firmax": -336,
                "firmay": 670,
                "firmaw": 140,
                "firmah": 34,
                "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
            }
            pdfJson = json.dumps(pdfJson)
            docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
            #
            context["codigo"] = randomString()
            context["urldown"] = "%s%s" % (
                settings.CONFIG_APP["AppFirma"],
                docCode
            )
            context["forma"] = "Firmando Cargo de Entrega Física"
            context["destino"] = destino
        return self.render_to_response(context=context)


class DocumentoRecibirFisicoQR(TemplateValidaLogin, TemplateView):
    template_name = "campos/blank.html"
    content_type = "image/png"

    def render_to_response(self, context, **response_kwargs):
        destino = Destino.objects.filter(pk=self.kwargs.get("pk")).first()
        if destino:
            destino.entregauid = uuid.uuid4().hex
            destino.entregauiduser = self.request.user
            destino.save()
            urlrecfis = "%s://%s%s" % (
                self.request.scheme,
                self.request.get_host(),
                reverse("apptra:documento_recibirf_qr_subir", kwargs={"codigo": destino.entregauid})
            )
            # qr = pyqrcode.create(urlrecfis, error="H")
            # qrLista = {
            #     "code": "MAD3",
            #     "title": "Evidencia",
            #     "url": urlrecfis
            # }
            qrLista = "MAD3|Evidencia|%s" % urlrecfis
            # qrLista = urlrecfis
            # qrJson = json.dumps(qrLista)
            # print(qrJson, type(qrJson))
            # qr = pyqrcode.create(base64.b64encode(qrJson.encode("ascii")).decode('ascii'), error="H")
            qr = pyqrcode.create(qrLista, error="H")
            qrbytes = io.BytesIO()
            qr.png(qrbytes, scale=10, module_color=(3, 94, 163, 255))
            qrimg = Image.open(qrbytes)
            logoruta = os.path.join(settings.STATICFILES_DIRS[0].__str__(), 'grc-192x192.png')
            logoimg = Image.open(logoruta)
            logoancho = 150
            logoalto = 150
            box = (
                int((qrimg.width - logoancho) / 2),
                int((qrimg.height - logoalto) / 2),
                int((qrimg.width - logoancho) / 2) + logoancho,
                int((qrimg.height - logoalto) / 2) + logoalto
            )
            logoimg = logoimg.resize((logoancho, logoalto))
            qrimg.paste(logoimg, box)
            qrbytes = io.BytesIO()
            qrimg.save(qrbytes, format=qrimg.format)
            return HttpResponse(qrbytes.getvalue())
        return super(DocumentoRecibirFisicoQR, self).render_to_response(context, **response_kwargs)


class DocumentoRecibirFisicoQRSubir(views.APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]
    # parser_classes = [FileUploadParser]
    http_method_names = "post"

    def post(self, request, format=None, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        destino = Destino.objects.filter(entregauid=codigo).first()
        if destino:
            archivos = request.FILES.getlist("file")
            if archivos:
                userid = destino.entregauiduser.pk
                destino.entregaimagen = archivos[0].read()
                destino.entregauid = None
                destino.entregauiduser = None
                destino.save()
                SocketMsg(
                    tipo="info",
                    clase="bg-info",
                    userid=userid,
                    titulo="OK",
                    mensaje="Se cargó la evidencia correctamente",
                    funcpost='EntFisEvidencia("Evidencia Cargada")'
                )
                return Response("La imagen se cargó correctamente", status=status.HTTP_200_OK)
            return Response("Debe subir un archivo imagen", status=status.HTTP_400_BAD_REQUEST)
        return Response("La url no es válida", status=status.HTTP_400_BAD_REQUEST)


class DocumentoRecibirFisicoBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        destino = Destino.objects.filter(pk=pk).first()
        if destino:
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            nombre = "CargoEntregaFisica.pdf"
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            # Creamos la plantilla y la enviamos al cliente
            eav = DocumentoRecibirFisicoVista(*args, **kwargs)
            eav.kwargs = self.kwargs
            eav.request = self.request
            context = self.get_renderer_context()
            context["responsable"] = PeriodoTrabajo.objects.get(pk=self.kwargs.get("ptid"))
            context["configapp"] = settings.CONFIG_APP
            response.write(eav.render_to_response(context=context).getvalue())
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoRecibirFisicoSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        destino = Destino.objects.filter(pk=pk).first()
        if destino:
            archivos = request.FILES.getlist("file")
            destino.entregauid = None
            destino.entregafisicacargo = archivos[0].read()
            destino.entregafisicafecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            destino.entregafisicareceptor = request.user.persona.periodotrabajoactual(
                request.session.get("cambioperiodo")
            )
            destino.save()
            ultimoestado = DestinoEstado(
                destino=destino,
                estado="RE",
                creador=self.request.user
            )
            ultimoestado.save()
            SocketMsg(
                tipo="info",
                clase="bg-dark",
                userid=self.request.user.pk,
                titulo="Bandeja Recepcionados",
                mensaje="Se recibió el documento correctamente",
                funcpost='refrescarTableros("dbEntrada,dbRecepcionados", true)'
            )
            mensaje = 'El documento ha sido recibido correctamente'
            SocketDocFir("RecFisOk", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class DocumentoRecibirFisicoError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        destino = Destino.objects.filter(pk=pk).first()
        if destino:
            destino.entregauid = None
            destino.save()
            mensaje = request.POST.get("mensaje")
            # Notificamos al cliente
            SocketDocFir("RecFisError", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class DocumentoRecFisDoc(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        doc = self.kwargs.get("doc")
        des = self.kwargs.get("des")
        destino = Destino.objects.filter(documento_id=doc, pk=des).first()
        enbase64 = request.headers.get("Base64", "false").lower()
        if destino and destino.entregafisicafecha:
            nombre = destino.documento.nombreDocumentoPdf()
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            if enbase64 == "true":
                response.write(base64.b64encode(destino.entregafisicacargo).decode('utf-8'))
            else:
                response.write(destino.entregafisicacargo)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoRecibirFisicoMasivoGenerar(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/entrada/generar_cargo.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        codigos = eval(self.kwargs.get("codigos").replace("_", ","))
        destinos = Destino.objects.filter(id__in=codigos)
        if destinos.count() > 0:
            codigo = uuid.uuid4().hex
            destinos.update(entregauid=codigo)
            dochost = "%s://%s" % (
                self.request.scheme,
                self.request.get_host()
            )
            token, created = Token.objects.get_or_create(user=self.request.user)
            fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            responsable = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            dependencia = responsable.area.dependencia
            #
            pdfJson = {
                "token": token.key,
                "rutabajada": "%s%s" % (
                    dochost,
                    reverse("apptra:documento_recibirfm_b", kwargs={"codigo": codigo, "ptid": responsable.pk})
                ),
                "rutasubida": "%s%s" % (
                    dochost,
                    reverse("apptra:documento_recibirfm_s", kwargs={"codigo": codigo})
                ),
                "rutaerror": "%s%s" % (
                    dochost,
                    reverse("apptra:documento_recibirfm_e", kwargs={"codigo": codigo})
                ),
                "rutalogos": dochost,
                "logos": listalogos(),
                "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "ruc": dependencia.rucfirma,
                "dni": responsable.persona.numero,
                "pagina": 1,
                "expedientestamp": "",
                "numerostamp": "CARGO DE ENTREGA FÍSICA",
                "fechastamp": "%s, %s" % (
                    str(dependencia.ubigeo.Departamento()).title(),
                    format_date(
                        fecha, "dd 'de' MMMM 'de' Y", locale=settings.LANGUAGE_CODE
                    )
                ),
                "local": "%s - %s - %s" % (
                    dependencia.siglas,
                    responsable.area.siglas,
                    responsable.CargoCorto()
                ),
                "localfull": "%s - %s - %s" % (
                    dependencia.nombre,
                    responsable.area.nombre,
                    responsable.Cargo()
                ),
                "firmamasiva": True,
                "firmatitularavanzada": False,
                "esmultiple": False,
                "esmultipledestino": False,
                "modo": "FR",
                "razon": "Cargo de Recepción",
                "numerar": False,
                "stampposxy": True,
                "firmax": -336,
                "firmay": 670,
                "firmaw": 140,
                "firmah": 34,
                "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
            }
            pdfJson = json.dumps(pdfJson)
            docCode = base64.b64encode(pdfJson.encode("ascii")).decode('ascii')
            #
            context["codigo"] = randomString()
            context["urldown"] = "%s%s" % (
                settings.CONFIG_APP["AppFirma"],
                docCode
            )
        return self.render_to_response(context=context)


class DocumentoRecibirFisicoMasivoBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        destinos = Destino.objects.filter(entregauid=codigo)
        if destinos.count() > 0:
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
            # responsable = self.request.user.persona.periodotrabajoactual(
            #     self.request.session.get("cambioperiodo")
            # )
            responsable = PeriodoTrabajo.objects.get(pk=self.kwargs.get("ptid"))
            dependencia = responsable.area.dependencia
            configData = []
            for destino in destinos:
                fileNAME = "documento_%s.pdf" % destino.pk
                fileRUTA = "%s/%s" % (tempdir, fileNAME)
                eav = DocumentoRecibirFisicoVista(*args, **kwargs)
                eav.kwargs = {"pk": destino.pk}
                eav.request = self.request
                context = self.get_renderer_context()
                context["responsable"] = responsable
                context["configapp"] = settings.CONFIG_APP
                contPDF = eav.render_to_response(context=context).getvalue()
                filePDF = open(fileRUTA, "wb")
                filePDF.write(contPDF)
                filePDF.close()
                zipeado.write(fileRUTA, fileNAME)
                configData.append(
                    {
                        "codigo": destino.pk,
                        "titulo": destino.expedientenro,
                        "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                        "ruc": dependencia.rucfirma,
                        "dni": responsable.persona.numero,
                        "pagina": 1,
                        "expedientestamp": "",
                        "numerostamp": destino.documento.obtenerNumeroSiglas(),
                        "fechastamp": "%s, %s" % (
                            str(dependencia.ubigeo.Departamento()).title(),
                            format_date(
                                fecha, "dd 'de' MMMM 'de' Y", locale=settings.LANGUAGE_CODE
                            )
                        ),
                        "local": "%s - %s - %s" % (
                            dependencia.siglas,
                            responsable.area.siglas,
                            responsable.CargoCorto()
                        ),
                        "localfull": "%s - %s - %s" % (
                            dependencia.nombre,
                            responsable.area.nombre,
                            responsable.Cargo()
                        ),
                        "firmamasiva": False,
                        "firmatitularavanzada": False,
                        "esmultiple": False,
                        "esmultipledestino": False,
                        "modo": "FR",
                        "razon": "Cargo de Recepción",
                        "numerar": False,
                        "stampposxy": True,
                        "firmax": -336,
                        "firmay": 670,
                        "firmaw": 140,
                        "firmah": 34,
                        "novalidarfirmante": settings.CONFIG_APP.get("NoValidarFirmante", False)
                    }
                )
            fileConfig = "config.txt"
            fileRUTA = "%s/%s" % (tempdir, fileConfig)
            fileDest = open(fileRUTA, "w")
            fileDest.write(json.dumps({"documentos": configData}, ensure_ascii=False))
            fileDest.close()
            zipeado.write(fileRUTA, fileConfig)
            zipeado.close()
            response.write(open(file7z, "rb").read())
            os.remove(file7z)
            shutil.rmtree(tempdir)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoRecibirFisicoMasivoSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        destinos = Destino.objects.filter(entregauid=codigo)
        if destinos.count() > 0:
            destinos.update(entregauid=None)
            archivos = request.FILES.getlist("file")
            archivozip = archivos[0].read()
            stream7z = py7zr.SevenZipFile(io.BytesIO(archivozip), "r")
            _folderTmp = os.path.join(settings.TEMP_DIR, uuid.uuid4().hex)
            stream7z.extractall(path=_folderTmp)
            for _file in stream7z.files:
                _nombre, _extension = os.path.splitext(_file.filename)
                _codigoDocumento = int(_nombre.split("_")[1])
                _fileload = open(os.path.join(_folderTmp, _file.filename), "rb")
                _fileread = _fileload.read()
                _fileload.close()
                destino = Destino.objects.filter(pk=_codigoDocumento).first()
                if destino:
                    destino.entregafisicacargo = _fileread
                    destino.entregafisicafecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
                    destino.entregafisicareceptor = request.user.persona.periodotrabajoactual(
                        request.session.get("cambioperiodo")
                    )
                    destino.save()
            stream7z.close()
            shutil.rmtree(_folderTmp)
            mensaje = 'Los cargos de recepción han sido firmados correctamente'
            SocketDocFir("RecFisMasOk", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class DocumentoRecibirFisicoMasivoError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        codigo = self.kwargs.get("codigo")
        destinos = Destino.objects.filter(entregauid=codigo)
        if destinos.count() > 0:
            destinos.update(entregauid=None)
            mensaje = request.POST.get("mensaje")
            # Notificamos al cliente
            SocketDocFir("RecFisMasError", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)
