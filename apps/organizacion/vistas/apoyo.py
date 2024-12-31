"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Q, Value
from django.views.generic import TemplateView

from apps.inicio.models import Cargo
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.apoyo import ApoyoForm, ApoyoAutorizarForm
from apps.organizacion.models import PeriodoTrabajo
from apps.organizacion.tablas.apoyo import TablaApoyo
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEliminacion, VistaEdicion


class ApoyoInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/apoyo/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Apoyos"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["tablaApoyo"] = TablaApoyo()
        return self.render_to_response(context=context)


class ApoyoListar(FeedDataView):
    token = TablaApoyo.token

    def get_queryset(self):
        return super(ApoyoListar, self).get_queryset().annotate(
            userid=Value(self.request.user.pk)
        ).filter(
            Q(
                area=self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area,
                tipo__in=["AP"]
            )
            |
            Q(
                apoyoarea=self.request.user.persona.periodotrabajoactual(
                    self.request.session.get("cambioperiodo")
                ).area,
                tipo__in=["AP"]
            )
        )

    def sort_queryset(self, queryset):
        qs = super(ApoyoListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-creado")
        return qs


class ApoyoAgregar(VistaCreacion):
    template_name = "organizacion/apoyo/formulario.html"
    model = PeriodoTrabajo
    form_class = ApoyoForm

    def get_form(self, form_class=None):
        form = super(ApoyoAgregar, self).get_form(form_class)
        areaactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area
        #
        upt = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        form.instance.tipo = "AP"
        form.instance.area = upt.area
        form.instance.permisotramite = "O"
        form.instance.esjefemodo = "NO"
        form.instance.activo = False
        form.instance.esjefe = False
        form.instance.esapoyo = True
        form.instance.creador = self.request.user
        if upt.area.paracomisiones:
            form.instance.cargo = Cargo.objects.filter(esapoyo=True).first()
        form.fields["area"].initial = areaactual
        form.fields["area"].queryset = areaactual.PadreHijas()
        return form

    def form_valid(self, form):
        if form.cleaned_data["persona"].TrabajosActivos().filter(
            area=form.cleaned_data["area"]
        ).count() > 0:
            form.add_error(None, "No es posible seleccionar a una persona de la misma área. "
                                 "Comuníquese con el Administrador del Sistema.")
            return self.render_to_response(self.get_context_data(form=form))
        else:
            if not hasattr(form.instance, "cargo"):
                form.instance.cargo = form.instance.persona.ultimoperiodotrabajo.cargo
        return super(ApoyoAgregar, self).form_valid(form)


class ApoyoEditar(VistaEdicion):
    template_name = "organizacion/apoyo/formulario.html"
    model = PeriodoTrabajo
    form_class = ApoyoForm

    def get_form(self, form_class=None):
        form = super(ApoyoEditar, self).get_form(form_class)
        areaactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area
        form.fields["area"].queryset = areaactual.PadreHijas()
        pt = self.get_object()
        form.fields["area"].initial = pt.area
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            upt = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            form.instance.area = upt.area
            form.instance.editor = self.request.user
            if upt.area.paracomisiones:
                form.instance.cargo = Cargo.objects.filter(esapoyo=True).first()
            else:
                form.instance.cargo = form.cleaned_data["persona"].ultimoperiodotrabajo.cargo  # upt.cargo
            form.save()
        return self.render_to_response(context=context)


class ApoyoEliminar(VistaEliminacion):
    template_name = "organizacion/apoyo/eliminar.html"
    model = PeriodoTrabajo

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if not self.object.activo:
            _result = super(ApoyoEliminar, self).form_valid(form)
        else:
            _result = self.render_to_response(context)
        return _result


class ApoyoAutorizar(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/apoyo/autorizar.html"
    model = PeriodoTrabajo
    form_class = ApoyoAutorizarForm
    extra_context = {
        "botonguardartexto": "Autorizar"
    }

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.aprobador = self.request.user.persona.ultimoperiodotrabajo
            form.instance.activo = True
            form.save()
            self.object = form.instance
            context["form"] = form
        return self.render_to_response(context)
