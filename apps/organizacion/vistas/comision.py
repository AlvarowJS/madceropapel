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
from django.db.models import Q, Count, Value
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.generic import TemplateView
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from pytz import timezone as pytz_timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.models import Cargo
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.comision import FormComision, FormComisionDirecta, FormApoyoComision, \
    ComisionApoyoForm
from apps.organizacion.models import Area, Dependencia, AreaTipo, PeriodoTrabajo
from apps.organizacion.tablas.comision import TablaComision, TablaComisionDirecta, TablaApoyoComision
from apps.organizacion.tablas.comisionsolicitudes import TablaComisionSolicitudes
from apps.organizacion.tablas.integrante import TablaIntegrante, TablaIntegranteDirecta
from apps.organizacion.vistas.varios import listalogos
from apps.sockets.vistas.mensajes import SocketDocFir, SocketMsg
from apps.tramite.models import Documento
from apps.tramite.vistas.plantillas.comision import ComisionAutorizacionVista
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion
from modulos.utiles.clases.varios import randomString


class ComisionInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/comision/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Comisiones"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["tablaComision"] = TablaComision()
        context["tablaIntegrante"] = TablaIntegrante()
        if request.user.is_staff:
            context["tablaComisionSolicitudes"] = TablaComisionSolicitudes()
            #
            context["tablaComisionDirecta"] = TablaComisionDirecta()
            context["tablaIntegranteDirecta"] = TablaIntegranteDirecta()
            # Apoyos de Comisión
            context["formApoyoComision"] = FormApoyoComision()
            context["tablaApoyoComision"] = TablaApoyoComision()
        return self.render_to_response(context=context)


class ComisionListar(FeedDataView):
    token = TablaComision.token

    def get_queryset(self):
        qs = Area.objetos.filter(
            areatipo__paracomision=True,
            # comisiondirecta=False
        ).exclude(
            padre__isnull=True
        ).annotate(
            user_id=Value(self.request.user.id),
            esstaff=Value(self.request.user.is_staff),
            esapoyo=Value(self.request.user.persona.ultimoperiodotrabajo.esapoyo),
            creaciones=Count(
                "trabajadores",
                filter=Q(
                    Q(
                        Q(trabajadores__creador=self.request.user)
                        |
                        Q(
                            trabajadores__creador__persona__ultimoperiodotrabajo__area=self.request.user.persona.ultimoperiodotrabajo.area,
                            esapoyo=True
                        )
                    ),
                    Q(
                        Q(jefeactual__persona__ultimoperiodotrabajo__area=self.request.user.persona.ultimoperiodotrabajo.area)
                        |
                        Q(trabajadores__activo=False, trabajadores__aprobador__isnull=True)
                    )
                )
            )
        ).filter(
            Q(
                creador=self.request.user,
                jefeactual__area=self.request.user.persona.ultimoperiodotrabajo.area
            )
            |
            Q(creaciones__gt=0)
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(ComisionListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class ComisionAgregar(VistaCreacion):
    template_name = "organizacion/comision/formulario.html"
    model = Area
    form_class = FormComision

    def get_form(self, form_class=None):
        form = super(ComisionAgregar, self).get_form(form_class)
        areaactual = self.request.user.persona.ultimoperiodotrabajo.area
        form.fields["comision"].queryset = form.fields["comision"].queryset.exclude(
            pk__in=Area.objetos.filter(
                areatipo__paracomision=True
            ).exclude(
                padre__isnull=True
            ).annotate(
                creaciones=Count(
                    "trabajadores",
                    filter=Q(creador=self.request.user)
                ),
                presidentes=Count(
                    "trabajadores",
                    filter=Q(trabajadores__persona=self.request.user.persona)
                ),
                creadores=Count(
                    "trabajadores",
                    filter=Q(trabajadores__creador=self.request.user)
                ),
                user_id=Value(self.request.user.id)
            ).filter(
                Q(creador=self.request.user)
                |
                Q(creaciones__gt=0)
                |
                Q(presidentes__gt=0)
                |
                Q(creadores__gt=0)
            ).values_list("id")
        )
        form.fields["cargo"].initial = form.fields["cargo"].queryset.first()
        form.fields["documentooficina"].initial = areaactual
        if self.request.user.persona.ultimoperiodotrabajo.esapoyo:
            form.fields["presidente"].queryset = form.fields["presidente"].queryset.filter(
                pk__in=self.request.user.persona.ultimoperiodotrabajo.area.trabajadores.values_list("persona_id")
            )
        else:
            del form.fields["presidente"]
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            presidente = form.cleaned_data.get("presidente")
            if not presidente:
                presidente = self.request.user.persona
            if form.cleaned_data["modocrea"] == "EX":
                pt = PeriodoTrabajo(
                    area=form.cleaned_data["comision"],
                    inicio=timezone.make_aware(
                        datetime.datetime.combine(
                            datetime.datetime.now().date(),
                            datetime.datetime.min.time()
                        )
                    ),
                    persona=presidente,
                    cargo=form.cleaned_data["cargo"],
                    permisotramite="O",
                    esjefe=True,
                    activo=False,
                    esjefemodo="TI",
                    documentosustento=form.cleaned_data["documentosustento"],
                    creador=self.request.user
                )
                pt.save()
            else:
                form.instance.presidente = presidente
                form.instance.dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
                form.instance.padre = Area.objects.get(pk=1)
                form.instance.areatipo = AreaTipo.objects.filter(paracomision=True).first()
                form.instance.activo = False
                form.instance.paracomisiones = True
                form.instance.creador = self.request.user
                form.instance.cargooficial = form.cleaned_data["cargo"]
                form.save()
                pt = PeriodoTrabajo(
                    area=form.instance,
                    inicio=timezone.make_aware(
                        datetime.datetime.combine(
                            datetime.datetime.now().date(),
                            datetime.datetime.min.time()
                        )
                    ),
                    persona=presidente,
                    cargo=form.cleaned_data["cargo"],
                    esjefe=True,
                    esjefemodo="TI",
                    activo=False,
                    permisotramite="O",
                    documentosustento=form.cleaned_data["documentosustento"],
                    creador=self.request.user
                )
                pt.save()
                self.object = form.instance
                self.object.jefeactual = pt
                self.object.save()
            context["form"] = form
        return self.render_to_response(context)


class ComisionEditar(VistaEdicion):
    template_name = "organizacion/comision/formulario.html"
    model = Area
    form_class = FormComision

    def get_form(self, form_class=None):
        form = super(ComisionEditar, self).get_form(form_class)
        presidente = self.get_object().jefeactual
        form.fields["presidente"].queryset = form.fields["presidente"].queryset.filter(
            pk__in=self.request.user.persona.ultimoperiodotrabajo.area.trabajadores.values_list("persona_id")
        )
        form.fields["presidente"].initial = presidente.persona
        if presidente.documentosustento:
            form.fields["documentooficina"].initial = presidente.documentosustento.documentotipoarea.area
            form.fields["documentotipo"].initial = presidente.documentosustento.documentotipoarea
        # form.fields["documentosustento"].queryset = Documento.objetos.annotate(
        #     c=Count("periodotrabajo")
        # ).filter(
        #     Q(c=0)
        #     |
        #     Q(pk=presidente.documentosustento.pk)
        # )
        form.fields["documentosustento"].initial = presidente.documentosustento
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.editor = self.request.user
            form.instance.cargooficial = form.cleaned_data["cargo"]
            form.save()
            pt = form.instance.trabajadores.order_by("pk").first()
            pt.persona = form.cleaned_data["presidente"]
            pt.cargo = form.cleaned_data["cargo"]
            pt.editor = self.request.user
            pt.save()
            self.object = form.instance
            self.object.jefeactual = pt
            self.object.save()
            context["form"] = form
        return self.render_to_response(context)


class ComisionEliminar(VistaEliminacion):
    template_name = "organizacion/comision/eliminar.html"
    model = Area

    def form_valid(self, form):
        comision = self.get_object()
        comision.jefeactual = None
        comision.save()
        comision.trabajadores.all().delete()
        comision.documentotipoarea_set.all().delete()
        return super(ComisionEliminar, self).form_valid(form)


class ComisionAutorizarGenerar(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/comision/firmar.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        comision = Area.objects.filter(pk=self.kwargs.get("pk")).first()
        if comision:
            #
            if comision.trabajadores.count() < 2:
                context["error"] = "Debe registrar al menos 02 integrantes"
            else:
                dochost = "%s://%s" % (
                    self.request.scheme,
                    self.request.get_host()
                )
                token, created = Token.objects.get_or_create(user=self.request.user)
                fecha = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
                dependencia = self.request.user.persona.ultimoperiodotrabajo.area.dependencia
                # responsable = self.request.user.persona.ultimoperiodotrabajo
                responsable = comision.jefeactual
                pdfJson = {
                    "token": token.key,
                    "rutabajada": "%s%s" % (
                        dochost,
                        reverse("apporg:comision_autorizar_bajar", kwargs={"pk": comision.pk})
                    ),
                    "rutasubida": "%s%s" % (
                        dochost,
                        reverse("apporg:comision_autorizar_subir", kwargs={"pk": comision.pk})
                    ),
                    "rutaerror": "%s%s" % (
                        dochost,
                        reverse("apporg:comision_autorizar_error", kwargs={"pk": comision.pk})
                    ),
                    "rutalogos": dochost,
                    "logos": listalogos(),
                    "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    "ruc": dependencia.rucfirma,
                    "dni": responsable.persona.numero,
                    "pagina": 1,
                    "expedientestamp": "",
                    "numerostamp": "AUTORIZACIÓN DE COMISIÓN",
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
                    "razon": "Doy Fe",
                    "numerar": False,
                    "stampposxy": True,
                    "firmax": -380,
                    "firmay": 552,
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
                context["forma"] = "Firmando Autorización de Comisión"
                context["comision"] = comision
        return self.render_to_response(context=context)


class ComisionAutorizarBajar(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        comision = Area.objects.filter(pk=pk).first()
        if comision:
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            nombre = "AutorizacionComision.pdf"
            response["Content-Disposition"] = "attachment; filename=%s" % nombre
            # Creamos la plantilla y la enviamos al cliente
            eav = ComisionAutorizacionVista(*args, **kwargs)
            eav.kwargs = self.kwargs
            eav.request = self.request
            context = self.get_renderer_context()
            context["configapp"] = settings.CONFIG_APP
            response.write(eav.render_to_response(context=context).getvalue())
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class ComisionAutorizarSubir(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        comision = Area.objects.filter(pk=pk).first()
        if comision:
            archivos = request.FILES.getlist("file")
            comision.documentoautorizacion = archivos[0].read()
            comision.activo = True
            comision.save()
            comision.trabajadores.update(activo=True, aprobador=request.user.persona.ultimoperiodotrabajo)
            # Notificamos al cliente
            mensaje = 'La autorización de comisión se ha firmado correctamente'
            SocketDocFir("ComOk", request.user.id, mensaje)
            # Si el cliente es diferente del presidente de la comisión
            # También lo notificamos
            if request.user != comision.creador:
                SocketMsg(
                    userid=comision.creador.pk,
                    funcpost='refrescar_tablaComision()'
                )
        return Response([], status=status.HTTP_200_OK)


class ComisionAutorizarError(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        comision = Area.objects.filter(pk=self.kwargs.get("pk"))
        if comision:
            mensaje = request.POST.get("mensaje")
            # Notificamos al cliente
            SocketDocFir("ComError", request.user.id, mensaje)
        return Response([], status=status.HTTP_200_OK)


# COMISIONES 2021
class ComisionDirectaListar(FeedDataView):
    token = TablaComisionDirecta.token

    def get_queryset(self):
        qs = Area.objetos.filter(
            areatipo__paracomision=True,
            comisiondirecta=True
        ).exclude(
            padre__isnull=True
        ).annotate(
            creaciones=Count(
                "trabajadores",
                filter=Q(
                    Q(
                        Q(trabajadores__creador=self.request.user)
                        |
                        Q(trabajadores__creador__persona__ultimoperiodotrabajo__area=self.request.user.persona.ultimoperiodotrabajo.area)
                    ),
                    Q(
                        Q(jefeactual__persona__ultimoperiodotrabajo__area=self.request.user.persona.ultimoperiodotrabajo.area)
                        |
                        Q(trabajadores__activo=False, trabajadores__aprobador__isnull=True)
                    )
                )
            ),
            user_id=Value(self.request.user.id),
            esstaff=Value(self.request.user.is_staff)
        ).filter(
            Q(
                esstaff=True
            )
            |
            Q(
                creador=self.request.user,
                jefeactual__area=self.request.user.persona.ultimoperiodotrabajo.area
            )
            |
            Q(creaciones__gt=0)
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(ComisionDirectaListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class ComisionDirectaAgregar(VistaCreacion):
    template_name = "organizacion/comision/formulariodirecta.html"
    model = Area
    form_class = FormComisionDirecta

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            presidente = form.cleaned_data.get("presidente")
            form.instance.presidente = presidente
            form.instance.dependencia = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"])
            form.instance.padre = Area.objects.get(pk=1)
            form.instance.areatipo = AreaTipo.objects.filter(paracomision=True).first()
            form.instance.activo = True
            form.instance.paracomisiones = True
            form.instance.cargooficial = form.cleaned_data["cargo"]
            form.instance.creador = self.request.user
            form.instance.comisiondirecta = True
            form.save()
            pt = PeriodoTrabajo(
                area=form.instance,
                inicio=timezone.make_aware(
                    datetime.datetime.combine(
                        datetime.datetime.now().date(),
                        datetime.datetime.min.time()
                    )
                ),
                persona=presidente,
                cargo=form.cleaned_data["cargo"],
                activo=True,
                permisotramite="O",
                esjefemodo="TI",
                esjefe=True,
                creador=self.request.user
            )
            pt.save()
            self.object = form.instance
            self.object.jefeactual = pt
            self.object.save()
            context["form"] = form
        return self.render_to_response(context)


class ComisionDirectaEditar(VistaEdicion):
    template_name = "organizacion/comision/formulariodirecta.html"
    model = Area
    form_class = FormComisionDirecta

    def get_form(self, form_class=None):
        form = super(ComisionDirectaEditar, self).get_form(form_class)
        presidente = self.get_object().jefeactual
        form.fields["presidente"].initial = presidente.persona
        form.fields["cargo"].initial = presidente.cargo
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.editor = self.request.user
            form.save()
            pt = form.instance.trabajadores.order_by("pk").first()
            pt.cargo = form.cleaned_data["cargo"]
            pt.persona = form.cleaned_data["presidente"]
            pt.editor = self.request.user
            pt.save()
            self.object = form.instance
            self.cargooficial = form.cleaned_data["cargo"]
            self.object.jefeactual = pt
            self.object.save()
            context["form"] = form
        return self.render_to_response(context)


class ComisionDirectaEliminar(VistaEliminacion):
    template_name = "organizacion/comision/eliminar.html"
    model = Area

    def get_context_data(self, **kwargs):
        context = super(ComisionDirectaEliminar, self).get_context_data(**kwargs)
        context["directa"] = True
        return context

    def form_valid(self, form):
        comision = self.get_object()
        comision.jefeactual = None
        comision.save()
        comision.trabajadores.all().delete()
        comision.documentotipoarea_set.all().delete()
        return super(ComisionDirectaEliminar, self).form_valid(form)


class ComisionApoyoListar(FeedDataView):
    token = TablaApoyoComision.token

    def get_queryset(self):
        qs = super(ComisionApoyoListar, self).get_queryset()
        qs = qs.filter(
            area_id=self.kwargs.get("pk"),
            esapoyo=True,
            tipo="AP"
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(ComisionApoyoListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class ComisionApoyoAgregar(VistaCreacion):
    template_name = "organizacion/comision/apoyo/formulario.html"
    model = PeriodoTrabajo
    form_class = ComisionApoyoForm

    def get_form(self, form_class=None):
        form = super(ComisionApoyoAgregar, self).get_form(form_class)
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.area_id = self.kwargs.get("pk")
            form.instance.esapoyo = True
            form.instance.tipo = "AP"
            form.instance.permisotramite = "O"
            form.instance.cargo = Cargo.objects.filter(esapoyo=True).first()
            form.instance.creador = self.request.user
            form.save()
            # self.object = form.instance
        context["form"] = form
        return self.render_to_response(context)


class ComisionApoyoEditar(VistaEdicion):
    template_name = "organizacion/comision/apoyo/formulario.html"
    model = PeriodoTrabajo
    form_class = ComisionApoyoForm

    def get_form(self, form_class=None):
        form = super(ComisionApoyoEditar, self).get_form(form_class)
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.editor = self.request.user
            form.save()
        context["form"] = form
        return self.render_to_response(context)


class ComisionApoyoEliminar(VistaEliminacion):
    template_name = "organizacion/comision/apoyo/eliminar.html"
    model = PeriodoTrabajo
