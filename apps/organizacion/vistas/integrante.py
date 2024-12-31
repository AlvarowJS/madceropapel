"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from django.db.models import Value, Q, Count
from django.utils import timezone

from apps.organizacion.formularios.integrante import FormIntegrante, FormIntegranteCambiar
from apps.organizacion.models import PeriodoTrabajo, Area
from apps.organizacion.tablas.integrante import TablaIntegrante, TablaIntegranteDirecta
from apps.tramite.models import Documento
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion


class IntegranteListar(FeedDataView):
    token = TablaIntegrante.token

    def get_queryset(self):
        qs = super(IntegranteListar, self).get_queryset()
        comid = self.kwargs.get("comid")
        if comid == 0:
            comid = -1
        qs = qs.filter(
            area_id=comid
        ).annotate(
            user_id=Value(self.request.user.id)
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(IntegranteListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-activo", "cargo_id", "-inicio")
        return qs


class IntegranteAgregar(VistaCreacion):
    template_name = "organizacion/integrante/formulario.html"
    model = PeriodoTrabajo
    form_class = FormIntegrante

    def get_form(self, form_class=None):
        form = super(IntegranteAgregar, self).get_form(form_class)
        form.fields["persona"].queryset = form.fields["persona"].queryset.exclude(
            pk__in=Area.objects.get(pk=self.kwargs.get("comid")).trabajadores.filter(
                Q(activo=True)
                |
                Q(activo=False, area__documentoautorizacion__isnull=True)
            ).values_list("persona_id")
        )
        form.fields["cargo"].queryset = form.fields["cargo"].queryset.exclude(
            pk__in=Area.objects.get(pk=self.kwargs.get("comid")).trabajadores.values_list("cargo_id"),
            esprincipal=True
        )
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.area_id = self.kwargs.get("comid")
            form.instance.permisotramite = "O"
            form.instance.activo = False
            form.instance.esjefe = False
            form.instance.inicio = timezone.make_aware(
                datetime.datetime.combine(
                    datetime.datetime.now().date(),
                    datetime.datetime.min.time()
                )
            )
            form.instance.creador = self.request.user
            form.save()
            context["form"] = form
        return self.render_to_response(context)


class IntegranteEditar(VistaEdicion):
    template_name = "organizacion/integrante/formulario.html"
    model = PeriodoTrabajo
    form_class = FormIntegrante

    def get_form(self, form_class=None):
        form = super(IntegranteEditar, self).get_form(form_class)
        form.fields["cargo"].queryset = form.fields["cargo"].queryset.exclude(
            pk__in=self.get_object().area.trabajadores.exclude(
                pk=self.get_object().pk
            ).values_list("cargo_id"),
            esprincipal=True
        )
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.editor = self.request.user
            form.save()
            context["form"] = form
        return self.render_to_response(context)


class IntegranteQuitar(VistaEliminacion):
    template_name = "organizacion/integrante/eliminar.html"
    model = PeriodoTrabajo


class IntegranteCambiar(VistaEdicion):
    template_name = "organizacion/integrante/cambiar.html"
    model = PeriodoTrabajo
    form_class = FormIntegranteCambiar

    def get_form(self, form_class=None):
        form = super(IntegranteCambiar, self).get_form(form_class)
        form.fields["persona"].queryset = form.fields["persona"].queryset.exclude(
            pk__in=self.get_object().area.trabajadores.filter(
                activo=True
            ).values_list("persona_id")
        )
        if not form.instance.cargo.esprincipal:
            del form.fields["documentoanio"]
            del form.fields["documentooficina"]
            del form.fields["documentotipo"]
            del form.fields["documentosustento"]
        else:
            form.fields["documentosustento"].queryset = Documento.objetos.annotate(
                c=Count("periodotrabajo")
            ).filter(
                c=0
            )
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            cldt = form.cleaned_data
            cldt["cargo"] = form.instance.cargo
            espresidente = cldt["cargo"].esprincipal
            formnew = FormIntegranteCambiar(data=cldt)
            if not espresidente:
                del formnew.fields["documentoanio"]
                del formnew.fields["documentooficina"]
                del formnew.fields["documentotipo"]
                del formnew.fields["documentosustento"]
            formnew.instance.area = form.instance.area
            formnew.instance.cargo = form.instance.cargo
            formnew.instance.poscargo = form.instance.poscargo
            formnew.instance.permisotramite = "O"
            formnew.instance.activo = not espresidente
            formnew.instance.inicio = timezone.now().date()
            formnew.instance.creador = self.request.user
            formnew.is_valid()
            formnew.save()
            #
            if not espresidente:
                formold = PeriodoTrabajo.objects.get(pk=form.instance.pk)
                formold.editor = self.request.user
                formold.fin = formnew.instance.inicio
                formold.aprobador = self.request.user.persona.periodotrabajoactual(
                    self.request.session.get("cambioperiodo"))
                formold.actualizado = timezone.now()
                formold.activo = False
                formold.save()
            context["form"] = form
        return self.render_to_response(context)


class IntegranteDirectaListar(FeedDataView):
    token = TablaIntegranteDirecta.token

    def get_queryset(self):
        qs = super(IntegranteDirectaListar, self).get_queryset()
        qs = qs.filter(
            area_id=self.kwargs.get("comid")
        ).annotate(
            user_id=Value(self.request.user.id)
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(IntegranteDirectaListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-activo", "-cargo__esprincipal", "cargo__nombrem", "-inicio")
        return qs


class IntegranteDirectaAgregar(VistaCreacion):
    template_name = "organizacion/integrante/formulariodirecto.html"
    model = PeriodoTrabajo
    form_class = FormIntegrante

    def get_form(self, form_class=None):
        form = super(IntegranteDirectaAgregar, self).get_form(form_class)
        form.fields["persona"].queryset = form.fields["persona"].queryset.exclude(
            pk__in=Area.objects.get(pk=self.kwargs.get("comid")).trabajadores.filter(
                Q(activo=True)
                |
                Q(activo=False, area__documentoautorizacion__isnull=True)
            ).values_list("persona_id")
        )
        form.fields["cargo"].queryset = form.fields["cargo"].queryset.filter(
            esprincipal=False
        )
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.area_id = self.kwargs.get("comid")
            form.instance.permisotramite = "O"
            form.instance.activo = True
            form.instance.esjefe = False
            form.instance.inicio = timezone.make_aware(
                datetime.datetime.combine(
                    datetime.datetime.now().date(),
                    datetime.datetime.min.time()
                )
            )
            form.instance.creador = self.request.user
            form.save()
            context["form"] = form
        return self.render_to_response(context)


class IntegranteDirectaEditar(VistaEdicion):
    template_name = "organizacion/integrante/formulariodirecto.html"
    model = PeriodoTrabajo
    form_class = FormIntegrante

    def get_form(self, form_class=None):
        form = super(IntegranteDirectaEditar, self).get_form(form_class)
        form.fields["cargo"].queryset = form.fields["cargo"].queryset.filter(
            Q(esprincipal=False)
            |
            Q(pk=self.get_object().pk)
        )
        return form

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.editor = self.request.user
            form.save()
            context["form"] = form
        return self.render_to_response(context)


class IntegranteDirectaQuitar(VistaEliminacion):
    template_name = "organizacion/integrante/eliminardirecto.html"
    model = PeriodoTrabajo

