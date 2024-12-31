"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import ProtectedError, Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, FormView
from django_select2.views import AutoResponseView
from pytz import timezone as pytz_timezone

from apps.inicio.models import PersonaConfiguracion
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.inicio.vistas.login import CerrarSesion
from apps.organizacion.formularios.trabajador import FormPeriodoTrabajo, FormTrabajadorSelector, \
    FormPeriodoTrabajoPassword, FormPeriodoTrabajoRotar, FormPeriodoTrabajoLogout, FormPeriodoTrabajoBaja
from apps.organizacion.models import PeriodoTrabajo, Area, TrabajadoresActuales
from apps.organizacion.tablas.trabajador import TablaTrabajadores
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEliminacion, VistaEdicion


class TrabajadorInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/trabajador/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Trabajadores"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = FormTrabajadorSelector()
        context["tablaTrabajadores"] = TablaTrabajadores()
        return self.render_to_response(context=context)


class TrabajadorAreaListar(AutoResponseView):
    def get_queryset(self):
        qs = self.widget.filter_queryset(
            self.request,
            self.term,
            self.queryset
        )
        cbdep = self.request.GET.get("cbtdep")
        if not cbdep:
            cbdep = self.request.GET.get("cbdep")
        if str(cbdep).startswith("0"):
            qs = qs.exclude(rindentepadre__isnull=False)
        elif cbdep:
            qs = qs.filter(rindentepadre_id=int(cbdep))
        return qs


class TrabajadorListar(FeedDataView):
    token = TablaTrabajadores.token

    def get_queryset(self):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        qs = super(TrabajadorListar, self).get_queryset().filter(
            area__paracomisiones=False,
            inicio__lte=fechaActual,
            activo=True
        ).filter(
            Q(fin=None)
            |
            Q(fin__gte=fechaActual)
        )
        if self.kwargs.get("todos") == 0:
            qs = qs.filter(
                area_id=self.kwargs.get("area")
            )
        return qs


class TrabajadorAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "organizacion/trabajador/formulario.html"
    model = PeriodoTrabajo
    form_class = FormPeriodoTrabajo
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def get_form(self, form_class=None):
        form = super(TrabajadorAgregar, self).get_form(form_class)
        if not settings.CONFIG_APP["LDAP"].get("STATUS"):
            del form.fields["usuariodominio"]
        form.instance.area_id = self.kwargs.get("area")
        return form

    def get_context_data(self, **kwargs):
        context = super(TrabajadorAgregar, self).get_context_data(**kwargs)
        if self.kwargs.get("area") == 0:
            context["noArea"] = True
            context["noBotonGuardar"] = True
            context["botoncancelartexto"] = "Aceptar"
        else:
            context["area"] = Area.objects.get(pk=self.kwargs.get("area"))
        return context

    def form_valid(self, form):
        if form.is_valid():
            # Verificamos si la persona ya está en un puesto de trabajo
            trabajando = TrabajadoresActuales().filter(persona=form.instance.persona).first()
            if trabajando:
                form.add_error(
                    None,
                    "El DNI indicado ya está registrado como <strong>%s</strong> en <strong>%s</strong>" % (
                        trabajando.Cargo(),
                        trabajando.area.nombre
                    )
                )
            else:
                form.instance.area_id = self.kwargs.get("area")
                super(TrabajadorAgregar, self).form_valid(form)
                # Actualizamos los otros datos de la persona
                persona = form.instance.persona
                perconf = PersonaConfiguracion.objects.filter(persona=persona).first()
                if not perconf:
                    perconf = PersonaConfiguracion(
                        persona=persona,
                        creador=self.request.user,
                        cambiarpassword=True
                    )
                    perconf.save()
                perconf.correoinstitucional = form.cleaned_data.get("correoinstitucional")
                if settings.CONFIG_APP["LDAP"].get("STATUS"):
                    perconf.usuariodominio = form.cleaned_data.get("usuariodominio")
                perconf.save()
                # Creamos el usuario
                usuario = persona.usuario
                if not usuario:
                    usuario = User(username=persona.numero)
                usuario.set_password(usuario.username)
                usuario.save()
                persona.usuario = usuario
                persona.save()
        return self.render_to_response(self.get_context_data(form=form))


class TrabajadorEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/trabajador/formulario.html"
    model = PeriodoTrabajo
    form_class = FormPeriodoTrabajo
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def get_initial(self):
        initial = super(TrabajadorEditar, self).get_initial()
        initial["personadni"] = self.get_object().persona.numero
        if hasattr(self.get_object().persona, "personaconfiguracion"):
            initial["correoinstitucional"] = self.get_object().persona.personaconfiguracion.correoinstitucional
            initial["usuariodominio"] = self.get_object().persona.personaconfiguracion.usuariodominio
        return initial

    def get_form(self, form_class=None):
        form = super(TrabajadorEditar, self).get_form(form_class)
        if not settings.CONFIG_APP["LDAP"].get("STATUS"):
            del form.fields["usuariodominio"]
        return form

    def form_valid(self, form):
        if form.is_valid():
            trabajando = None
            personaAnterior = PeriodoTrabajo.objects.get(pk=self.get_object().pk).persona
            if personaAnterior != form.instance.persona:
                # Verificamos si la persona ya está en un puesto de trabajo
                trabajando = TrabajadoresActuales().filter(
                    persona=form.instance.persona
                ).first()
            if trabajando:
                form.add_error(
                    None,
                    "El DNI indicado ya está registrado como <strong>%s</strong> en <strong>%s</strong>" % (
                        trabajando.cargo.nombre,
                        trabajando.area.nombre
                    )
                )
            else:
                super(TrabajadorEditar, self).form_valid(form)
                # Actualizamos los otros datos de la persona
                persona = form.instance.persona
                perconf = PersonaConfiguracion.objects.filter(persona=persona).first()
                if not perconf:
                    perconf = PersonaConfiguracion(
                        persona=persona,
                        creador=self.request.user,
                        cambiarpassword=True
                    )
                    perconf.save()
                perconf.correoinstitucional = form.cleaned_data.get("correoinstitucional")
                if settings.CONFIG_APP["LDAP"].get("STATUS"):
                    perconf.usuariodominio = form.cleaned_data.get("usuariodominio")
                perconf.save()
                # Creamos el usuario
                usuario = persona.usuario
                if not usuario:
                    usuario = User(username=persona.numero)
                    usuario.set_password(usuario.username)
                    usuario.save()
                    persona.usuario = usuario
                    persona.save()
        return self.render_to_response(self.get_context_data(form=form))


class TrabajadorEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "organizacion/trabajador/eliminar.html"
    model = PeriodoTrabajo

    def form_valid(self, form):
        pt = self.get_object()
        persona = pt.persona
        persona.ultimoperiodotrabajo = None
        persona.save(update_pt=False)
        try:
            _result = super(TrabajadorEliminar, self).form_valid(form)
        except ProtectedError as e:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            context["errordelete"] = "El registro no puede ser eliminado"
            _result = self.render_to_response(context)
        persona.save()
        return _result


class TrabajadorPassword(TemplateValidaLogin, FormView):
    template_name = "organizacion/trabajador/password.html"
    form_class = FormPeriodoTrabajoPassword
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def dispatch(self, request, *args, **kwargs):
        self.periodotrabajo = PeriodoTrabajo.objects.get(pk=self.kwargs.get("pk"))
        return super(TrabajadorPassword, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrabajadorPassword, self).get_context_data(**kwargs)
        context["object"] = self.periodotrabajo
        if not hasattr(self.periodotrabajo.persona, "usuario"):
            context["botonguardartexto"] = "Asignar"
        else:
            context["botonguardartexto"] = "Restablecer"
        return context

    def form_valid(self, form, ):
        usuario = None
        if hasattr(self.periodotrabajo.persona, "usuario"):
            usuario = self.periodotrabajo.persona.usuario
        if not usuario:
            usuario = User(username=self.periodotrabajo.persona.numero)
            usuario.save()
        self.periodotrabajo.persona.ReiniciarPassword()
        return self.render_to_response(self.get_context_data(form=form))


class TrabajadorRotar(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/trabajador/rotar.html"
    model = PeriodoTrabajo
    form_class = FormPeriodoTrabajoRotar
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def get_context_data(self, **kwargs):
        context = super(TrabajadorRotar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Rotar"
        return context

    def get_form(self, form_class=None):
        form = super(TrabajadorRotar, self).get_form(form_class)
        form.fields["area"].queryset = form.fields["area"].queryset.exclude(
            pk=self.get_object().area.pk
        )
        return form

    def form_valid(self, form):
        if form.is_valid():
            ta = PeriodoTrabajo.objects.get(pk=form.instance.pk)
            ta.fin = timezone.now()
            ta.activo = False
            ta.save()
            form.instance.pk = None
            form.save()
            CerrarSesion(ta.persona.usuario.id)
        return self.render_to_response(self.get_context_data(form=form))


class TrabajadorBaja(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/trabajador/baja.html"
    model = PeriodoTrabajo
    form_class = FormPeriodoTrabajoBaja
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def get_context_data(self, **kwargs):
        context = super(TrabajadorBaja, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Dar de Baja"
        context["OtrosTrabajos"] = self.get_object().persona.TrabajosActivos().exclude(pk=self.get_object().pk)
        return context

    def form_valid(self, form):
        if form.is_valid():
            fechaActual = timezone.now()
            persona = self.get_object().persona
            persona.TrabajosActivos().update(
                fin=fechaActual,
                activo=False
            )
            persona.ultimoperiodotrabajo = None
            persona.save()
            CerrarSesion(persona.usuario.id)
        return self.render_to_response(self.get_context_data(form=form))


class TrabajadorLogout(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/trabajador/logout.html"
    model = PeriodoTrabajo
    form_class = FormPeriodoTrabajoLogout
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]
    extra_context = {
        "botonguardartexto": "Cerrar Sesión"
    }

    def form_valid(self, form):
        if form.is_valid():
            CerrarSesion(self.get_object().persona.usuario.id)
        return self.render_to_response(self.get_context_data(form=form))
