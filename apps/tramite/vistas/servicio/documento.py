"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import json

from django.http import HttpRequest
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tramite.models import Documento, DocumentoPDF
from apps.tramite.vistas.seguimiento.consulta import SeguimientoNodo, SeguimientoInfo


class ServicioDocumentoValida(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        anio = self.kwargs.get("anio")
        numero = self.kwargs.get("numero")
        clave = self.kwargs.get("clave")
        doc = Documento.objects.filter(
            expediente__anio=anio,
            expediente__numero=numero,
            clave=clave
        ).first()
        if doc:
            docpdf = doc.documentoplantilla.documentopdf_set.first()
            if not docpdf and doc.des_documento.count() > 0:
                docpdf = DocumentoPDF.objects.create(
                    documentoplantilla=doc.documentoplantilla,
                    pdf=doc.documentoplantilla.contenido,
                    destino=doc.des_documento.order_by("creado").first(),
                    creador=doc.creador
                )
            if docpdf:
                datajson = {
                    "tipo": doc.origentipo
                }
                if doc.origentipo in ["O", "P"]:
                    datajson["doc"] = base64.b64encode(docpdf.pdffirma).decode('utf-8')
                else:
                    datajson["doc"] = base64.b64encode(docpdf.pdf).decode('utf-8')
                return Response(datajson, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ServicioSeguimientoExp(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        anio = self.kwargs.get("anio")
        numero = self.kwargs.get("numero")
        clave = self.kwargs.get("clave")
        doc = Documento.objects.filter(
            expediente__anio=anio,
            expediente__numero=numero
        ).exclude(ultimoestado__estado="AN").order_by("creado")
        if clave != "0":
            doc = doc.filter(
                clave=clave
            )
        doc = doc.first()
        if doc:
            datarpta = {
                "modo": "DOC",
                "expedientenro": doc.expedientenro,
                "origen": "general",
                "documentoid": doc.pk
            }
            nodoprim = doc.des_documento.exclude(
                ultimoestado__estado="AN"
            ).order_by("pk").first()
            if nodoprim:
                datarpta.update({
                    "nodoprimero": nodoprim.pk
                })
            return Response(datarpta, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ServicioSeguimientoNodo(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        sn = SeguimientoNodo()
        rpta = HttpRequest()
        rpta.method = "POST"
        rpta.user_agent = request.user_agent
        rpta.session = request.session
        rpta.user = request.user
        rpta.META = request.META
        data = request.data
        data["excanu"] = "AN"
        rpta.POST = data
        sn.request = rpta
        sn.kwargs = self.kwargs
        datajson = sn.post(request=rpta, *args, **kwargs)
        datajson.render()
        _result = json.loads(datajson.getvalue().decode("utf8"))
        return Response(_result, status=status.HTTP_200_OK)


class ServicioSeguimientoInfo(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        sn = SeguimientoInfo()
        rpta = HttpRequest()
        rpta.method = "POST"
        rpta.user_agent = request.user_agent
        rpta.session = request.session
        rpta.user = request.user
        rpta.META = request.META
        data = request.data
        data["excanu"] = "AN"
        rpta.POST = data
        sn.request = rpta
        sn.kwargs = self.kwargs
        datajson = sn.post(request=rpta, *args, **kwargs)
        datajson.render()
        _result = json.loads(datajson.getvalue().decode("utf8"))
        return Response(_result, status=status.HTTP_200_OK)
