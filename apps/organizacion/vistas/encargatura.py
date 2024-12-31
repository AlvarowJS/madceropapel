"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import datetime
import json

from babel.dates import format_date
from django.conf import settings
from django.db.models import Count, Q, Value
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from pytz import timezone as pytz_timezone
from django.views.generic import TemplateView
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.inicio.vistas.login import CerrarSesion
from apps.organizacion.formularios.encargatura import EncargaturaForm, EncargaturaPuestoForm, \
    EncargaturaPuestoTerminarForm
from apps.organizacion.models import PeriodoTrabajo
from apps.organizacion.tablas.encargatura import TablaEncargatura, TablaEncargaturaPuesto
from apps.organizacion.vistas.varios import listalogos
from apps.sockets.vistas.mensajes import SocketDocFir, SocketMsg
from apps.tramite.models import Documento
from apps.tramite.vistas.plantillas.encargatura import EncargaturaAutorizacionVista, EncargaturaAnulacionVista
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEliminacion, VistaEdicion
from modulos.utiles.clases.varios import randomString


class EncargaturaInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/encargatura/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Encargaturas"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["tablaEncargatura"] = TablaEncargatura()
        context["tablaEncargaturaPuesto"] = TablaEncargaturaPuesto()
        return self.render_to_response(context=context)


class EncargaturaListar(FeedDataView):
    token = TablaEncargatura.token

    def get_queryset(self):
        qs = super(EncargaturaListar, self).get_queryset()
        area = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area
        qs = qs.annotate(
            token=Value(self.request.user.auth_token.key)
        ).filter(
            tipo__in=["EN"]
        ).filter(
            Q(area=area)
            |
            Q(creador__persona__ultimoperiodotrabajo__area=area)
            |
            Q(
                Q(area_id__in=area.Hijas()),
                Q(
                    Q(creador=self.request.user)
                    |
                    Q(creador__persona__ultimoperiodotrabajo__area__in=area.PadreHijas())
                )
            )
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(EncargaturaListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class EncargaturaAgregar(VistaCreacion):
    template_name = "organizacion/encargatura/formulario.html"
    model = PeriodoTrabajo
    form_class = EncargaturaForm

    def get_form(self, form_class=None):
        form = super(EncargaturaAgregar, self).get_form(form_class)
        areaactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area
        #
        #
        form.fields["area"].initial = areaactual
        form.fields["area"].queryset = areaactual.PadreHijas()
        form.fields["documentooficina"].initial = areaactual
        form.fields["documentosustento"].queryset = Documento.objetos.filter(
            ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"],
            origentipo="O"
        ).order_by("-numero").annotate(
            # c=Count("periodotrabajo")
        ).filter(
            # c=0
        )
        return form

    def form_valid(self, form):
        if form.is_valid():
            upt = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            area = form.cleaned_data["area"]
            form.instance.tipo = "EN"
            form.instance.area = area
            form.instance.cargo = area.jefeactual.cargo
            form.instance.permisotramite = "O"
            form.instance.esjefemodo = "TE"
            form.instance.activo = False
            form.instance.esjefe = True
            form.instance.creador = self.request.user
        return super(EncargaturaAgregar, self).form_valid(form)


class EncargaturaEditar(VistaEdicion):
    template_name = "organizacion/encargatura/formulario.html"
    model = PeriodoTrabajo
    form_class = EncargaturaForm

    def get_form(self, form_class=None):
        form = super(EncargaturaEditar, self).get_form(form_class)
        areaactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area
        form.fields["area"].queryset = areaactual.PadreHijas()
        pt = self.get_object()
        form.fields["area"].initial = pt.area
        if pt.documentosustento:
            form.fields["documentoanio"].initial = pt.documentosustento.anio
            form.fields["documentooficina"].initial = pt.documentosustento.documentotipoarea.area
            form.fields["documentotipo"].initial = pt.documentosustento.documentotipoarea
            form.fields["documentosustento"].queryset = Documento.objetos.filter(
                ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"],
                origentipo="O"
            ).order_by("-numero").annotate(
                # c=Count("periodotrabajo")
            ).filter(
                # Q(c=0)
                # |
                Q(pk=pt.documentosustento.pk)
            )
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            # upt = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            area = form.cleaned_data["area"]
            form.instance.area = area
            form.instance.cargo = area.jefeactual.cargo
            form.instance.editor = self.request.user
            form.save()
        return self.render_to_response(context=context)


class EncargaturaEliminar(VistaEliminacion):
    template_name = "organizacion/encargatura/eliminar.html"
    model = PeriodoTrabajo

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if not self.object.activo:
            _result = super(EncargaturaEliminar, self).form_valid(form)
        else:
            _result = self.render_to_response(context)
        return _result


class EncargaturaFirmar(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/encargatura/firmar.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        encargatura = PeriodoTrabajo.objects.filter(pk=self.kwargs.get("pk")).first()
        if encargatura:
            #
            dochost = "%s://%s" % (
                self.request.scheme,
                self.request.get_host()
            )
            token, created = Token.objects.get_or_create(user=self.request.user)
            fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            periodoactual = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            dependencia = periodoactual.area.dependencia
            if periodoactual.area.Encargado() == periodoactual:
                responsable = periodoactual
            else:
                responsable = periodoactual.area.jefeactual
            pdfJson = {
                "token": token.key,
                "rutabajada": "%s%s" % (
                    dochost,
                    reverse("apporg:encargatura_firmar_bajar", kwargs={"pk": encargatura.pk, "ptid": responsable.pk})
                ),
                "rutasubida": "%s%s" % (
                    dochost,
                    reverse("apporg:encargatura_firmar_subir", kwargs={"pk": encargatura.pk})
                ),
                "rutaerror": "%s%s" % (
                    dochost,
                    reverse("apporg:encargatura_firmar_error", kwargs={"pk": encargatura.pk})
                ),
                "rutalogos": dochost,
                "logos": listalogos(),
                "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "ruc": dependencia.rucfirma,
                "dni": responsable.persona.numero,
                "pagina": 1,
                "expedientestamp": "",
                "numerostamp": "PERMISO DE ENCARGATURA",
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
                "modo": "FT",
                "razon": "Autorizo",
                "numerar": False,
                "stampposxy": True,
                "firmax": -380,
                "firmay": 470,
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
            context["forma"] = "Firmando Documento de Encargatura"
            context["encargatura"] = encargatura
        return self.render_to_response(context=context)


class EncargaturaFirmarBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        encargatura = PeriodoTrabajo.objects.filter(pk=pk).first()
        if encargatura:
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            nombre = "PermisoEncargatura.pdf"
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            # Creamos la plantilla y la enviamos al cliente
            eav = EncargaturaAutorizacionVista(*args, **kwargs)
            eav.kwargs = self.kwargs
            eav.request = self.request
            context = self.get_renderer_context()
            context["responsable"] = PeriodoTrabajo.objects.get(pk=self.kwargs.get("ptid"))
            context["configapp"] = settings.CONFIG_APP
            response.write(eav.render_to_response(context=context).getvalue())
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class EncargaturaFirmarSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        encargatura = PeriodoTrabajo.objects.filter(pk=pk).first()
        if encargatura:
            archivos = request.FILES.getlist("file")
            encargatura.activo = True
            encargatura.encargaturaplantilla = archivos[0].read()
            encargatura.save()
            # Notificamos al cliente
            mensaje = 'El documento de encargatura se ha firmado correctamente'
            SocketDocFir("EncOk", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class EncargaturaFirmarError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        encargatura = PeriodoTrabajo.objects.filter(pk=pk).first()
        if encargatura:
            mensaje = request.POST.get("mensaje")
            # Notificamos al cliente
            SocketDocFir("EncError", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


# ANULACION
class EncargaturaAnular(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/encargatura/firmaranular.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        encargatura = PeriodoTrabajo.objects.filter(pk=self.kwargs.get("pk")).first()
        if encargatura:
            #
            dochost = "%s://%s" % (
                self.request.scheme,
                self.request.get_host()
            )
            token, created = Token.objects.get_or_create(user=self.request.user)
            fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
            periodoactual = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            dependencia = periodoactual.area.dependencia
            responsable = periodoactual.area.jefeactual
            pdfJson = {
                "token": token.key,
                "rutabajada": "%s%s" % (
                    dochost,
                    reverse("apporg:encargatura_anular_bajar", kwargs={"pk": encargatura.pk, "ptid": responsable.pk})
                ),
                "rutasubida": "%s%s" % (
                    dochost,
                    reverse("apporg:encargatura_anular_subir", kwargs={"pk": encargatura.pk})
                ),
                "rutaerror": "%s%s" % (
                    dochost,
                    reverse("apporg:encargatura_anular_error", kwargs={"pk": encargatura.pk})
                ),
                "rutalogos": dochost,
                "logos": listalogos(),
                "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "ruc": dependencia.rucfirma,
                "dni": responsable.persona.numero,
                "pagina": 1,
                "expedientestamp": "",
                "numerostamp": "ANULACIÓN DE PERMISO DE ENCARGATURA",
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
                "modo": "FT",
                "razon": "Anulo Autorización",
                "numerar": False,
                "stampposxy": True,
                "firmax": -380,
                "firmay": 470,
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
            context["forma"] = "Anulando Documento de Encargatura"
            context["encargatura"] = encargatura
        return self.render_to_response(context=context)


class EncargaturaAnularBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        encargatura = PeriodoTrabajo.objects.filter(pk=pk).first()
        if encargatura:
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            nombre = "AnulacionEncargatura.pdf"
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            # Creamos la plantilla y la enviamos al cliente
            eav = EncargaturaAnulacionVista(*args, **kwargs)
            eav.kwargs = self.kwargs
            eav.request = self.request
            context = self.get_renderer_context()
            context["responsable"] = PeriodoTrabajo.objects.get(pk=self.kwargs.get("ptid"))
            context["configapp"] = settings.CONFIG_APP
            response.write(eav.render_to_response(context=context).getvalue())
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class EncargaturaAnularSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        encargatura = PeriodoTrabajo.objects.filter(pk=pk).first()
        if encargatura:
            archivos = request.FILES.getlist("file")
            encargatura.activo = False
            encargatura.encargaturaplantillaanulacion = archivos[0].read()
            encargatura.save()
            # Notificamos al cliente
            mensaje = 'El documento de anulación de encargatura se ha firmado correctamente'
            SocketDocFir("EncOk", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


class EncargaturaAnularError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        encargatura = PeriodoTrabajo.objects.filter(pk=pk).first()
        if encargatura:
            mensaje = request.POST.get("mensaje")
            # Notificamos al cliente
            SocketDocFir("EncError", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


# Encargatura por Puesto
class EncargaturaPuestoListar(FeedDataView):
    token = TablaEncargaturaPuesto.token

    def get_queryset(self):
        qs = super(EncargaturaPuestoListar, self).get_queryset()
        qs = qs.filter(
            tipo__in=["EP"]
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(EncargaturaPuestoListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class EncargaturaPuestoAgregar(VistaCreacion):
    template_name = "organizacion/encargatura/formulariopuesto.html"
    model = PeriodoTrabajo
    form_class = EncargaturaPuestoForm

    def get_form(self, form_class=None):
        form = super(EncargaturaPuestoAgregar, self).get_form(form_class)
        form.instance.tipo = "EP"
        # form.instance.cargo = upt.cargo
        form.instance.permisotramite = "O"
        form.instance.esjefemodo = "TE"
        form.instance.activo = True
        form.instance.esjefe = True
        form.instance.creador = self.request.user
        form.instance.inicio = timezone.make_aware(
            datetime.datetime.combine(
                datetime.datetime.now().date(),
                datetime.datetime.min.time()
            )
        )
        return form

    def form_valid(self, form):
        if form.is_valid():
            form.instance.cargo = form.cleaned_data["persona"].ultimoperiodotrabajo.cargo
        return super(EncargaturaPuestoAgregar, self).form_valid(form)


class EncargaturaPuestoTerminar(VistaEdicion):
    template_name = "organizacion/encargatura/formulariopuestoterminar.html"
    model = PeriodoTrabajo
    form_class = EncargaturaPuestoTerminarForm

    def get_context_data(self, **kwargs):
        context = super(EncargaturaPuestoTerminar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Terminar"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.fin = timezone.now()
            form.instance.activo = False
            form.save()
            CerrarSesion(form.instance.persona.usuario.pk)
            self.object = form.instance
        return self.render_to_response(self.get_context_data(form=form))


class EncargaturaCargoDoc(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        encargatura = PeriodoTrabajo.objects.filter(pk=self.kwargs.get("pk")).first()
        enbase64 = request.headers.get("Base64", "false").lower()
        if encargatura and encargatura.encargaturaplantilla:
            nombre = "Documento de Autorizacion de Encargatura"
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            if enbase64 == "true":
                response.write(base64.b64encode(encargatura.encargaturaplantilla).decode('utf-8'))
            else:
                response.write(encargatura.encargaturaplantilla)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class EncargaturaCargoDocAnu(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        encargatura = PeriodoTrabajo.objects.filter(pk=self.kwargs.get("pk")).first()
        enbase64 = request.headers.get("Base64", "false").lower()
        if encargatura and encargatura.encargaturaplantillaanulacion:
            nombre = "Documento de Anulacion de Encargatura"
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            if enbase64 == "true":
                response.write(base64.b64encode(encargatura.encargaturaplantillaanulacion).decode('utf-8'))
            else:
                response.write(encargatura.encargaturaplantillaanulacion)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)
