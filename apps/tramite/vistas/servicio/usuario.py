"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.models import Persona


class UsuarioLogin(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        dataresp = {
            "success": False
        }
        username = self.kwargs.get("username")
        password = self.kwargs.get("password")
        user = authenticate(request=None, username=username, password=password)
        if user is None:
            return Response(dataresp, status=status.HTTP_400_BAD_REQUEST)
        else:
            dataresp["success"] = True
            dataresp["id"] = user.pk
            return Response(dataresp, status=status.HTTP_200_OK)


class UsuarioInfo(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        dataresp = {
            "success": False
        }
        user = User.objects.filter(username=self.kwargs.get("dni")).first()
        if user is None:
            return Response(dataresp, status=status.HTTP_400_BAD_REQUEST)
        else:
            dataresp["success"] = True
            dataresp["id"] = user.pk
            dataresp["nombre"] = user.persona.nombrecompleto
            dataresp["oficinanombre"] = user.persona.ultimoperiodotrabajo.area.nombre
            dataresp["oficinaid"] = user.persona.ultimoperiodotrabajo.area.pk
            dataresp["dependencia"] = user.persona.ultimoperiodotrabajo.area.dependencia.nombre
            dataresp["dependenciaid"] = user.persona.ultimoperiodotrabajo.area.dependencia.pk
            return Response(dataresp, status=status.HTTP_200_OK)


class UsuarioToken(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        dataresp = {
            "success": False,
            "message": ""
        }
        statusresp = status.HTTP_400_BAD_REQUEST
        user = User.objects.filter(username=self.kwargs.get("dni")).first()
        if user:
            if user.persona.TrabajosActivos().count() > 0:
                key = None
                try:
                    key = user.auth_token.key
                except:
                    pass
                if key:
                    dataresp["success"] = True
                    dataresp["token"] = key
                    statusresp = status.HTTP_200_OK
                else:
                    dataresp["message"] = "No se pudo obtener el token"
            else:
                dataresp["message"] = "El dni no está registrado como trabajador"
        else:
            dataresp["message"] = "El dni no existe"
        return Response(dataresp, status=statusresp)
