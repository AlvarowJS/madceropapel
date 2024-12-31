"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView
from pytz import timezone as pytz_timezone

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.proyeccion import FormProyeccionTrabajadorSelector, FormProyeccion, \
    FormProyeccionArea
from apps.organizacion.models import Proyeccion, PeriodoTrabajo
from apps.organizacion.tablas.proyeccion import TablaProyeccion, TablaProyeccionArea
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEliminacion


class ProyeccionInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/proyeccion/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Proyecciones"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_staff:
            fpts = FormProyeccionTrabajadorSelector()
            fpts.fields["cbtrabajador"].initial = fpts.fields["cbtrabajador"].queryset.first()
            context["form"] = fpts
            context["tablaProyeccion"] = TablaProyeccion(trabajador=fpts.fields["cbtrabajador"].initial)
        else:
            context["tablaProyeccionArea"] = TablaProyeccionArea()
        return self.render_to_response(context=context)


class ProyeccionListar(FeedDataView):
    token = TablaProyeccion.token

    def get_queryset(self):
        qs = super(ProyeccionListar, self).get_queryset()
        qs = qs.filter(
            periodotrabajo_id=self.kwargs.get("pt")
        )
        return qs


class ProyeccionAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "organizacion/proyeccion/formulario.html"
    model = Proyeccion
    form_class = FormProyeccion

    def get_form(self, form_class=None):
        form = super(ProyeccionAgregar, self).get_form(form_class)
        form.fields["areasorigen"].queryset = form.fields["areasorigen"].queryset.exclude(
            pk__in=Proyeccion.objects.filter(
                periodotrabajo_id=self.kwargs.get("pt")
            ).values_list("areaorigen_id")
        ).exclude(
            pk=PeriodoTrabajo.objects.get(pk=self.kwargs.get("pt")).area_id
        )
        return form

    def form_valid(self, form):
        if form.is_valid():
            cldt = form.cleaned_data
            for area in cldt["areasorigen"]:
                proy = Proyeccion(
                    periodotrabajo_id=self.kwargs.get("pt"),
                    areaorigen=area,
                    creador=self.request.user
                )
                proy.save()
        return self.render_to_response(self.get_context_data(form=form))


class ProyeccionEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "organizacion/proyeccion/eliminar.html"
    model = Proyeccion


class ProyeccionAreaListar(FeedDataView):
    token = TablaProyeccionArea.token

    def get_queryset(self):
        qs = super(ProyeccionAreaListar, self).get_queryset()
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        qs = qs.filter(
            areaorigen=periodoactual.area,
            periodotrabajo__activo=True,
            periodotrabajo__inicio__lte=fechaActual
        ).filter(
            Q(periodotrabajo__fin__isnull=True)
            |
            Q(periodotrabajo__fin__gte=fechaActual)
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(ProyeccionAreaListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class ProyeccionAreaEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "organizacion/proyeccion/eliminararea.html"
    model = Proyeccion


class ProyeccionAreaAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "organizacion/proyeccion/formularioarea.html"
    model = Proyeccion
    form_class = FormProyeccionArea

    def get_form(self, form_class=None):
        form = super(ProyeccionAreaAgregar, self).get_form(form_class)
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        form.fields["trabajadores"].queryset = form.fields["trabajadores"].queryset.exclude(
            proyeccionareas__areaorigen=periodoactual.area
        )
        return form

    def form_valid(self, form):
        if form.is_valid():
            periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            cldt = form.cleaned_data
            for pt in cldt["trabajadores"]:
                proy = Proyeccion(
                    periodotrabajo=pt,
                    areaorigen=periodoactual.area,
                    creador=self.request.user
                )
                proy.save()
        return self.render_to_response(self.get_context_data(form=form))
