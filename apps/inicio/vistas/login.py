"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, \
    PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.contrib.sessions.models import Session
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView
from django_select2.views import AutoResponseView
from rest_framework.authtoken.models import Token

from apps.inicio.formularios.areachange import AreaChangeForm
from apps.inicio.formularios.login import InicioLoginForm, FormChangePassword, InicioResetPasswordForm, \
    InicioResetPasswordConfirmForm
from apps.inicio.vistas.inicio import TemplateConfig, TemplateValidaLogin
from apps.organizacion.models import PeriodoTrabajo


class InicioLogin(TemplateConfig, LoginView):
    template_name = "inicio/login/vista_azul.html"
    form_class = InicioLoginForm
    extra_context = {
        "eslogin": True
    }

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.path == reverse("appini:inicio_login"):
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        elif self.request.POST:
            self.template_name = "inicio/login/formulario.html"
        return super(InicioLogin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InicioLogin, self).get_context_data(**kwargs)
        if self.request.session.get("NoAccess") and \
                self.request.META.get("HTTP_REFERER") == context["current_site"] + "/":
            context["NoAccess"] = self.request.session["NoAccess"]
            del self.request.session["NoAccess"]
        return context

    def form_valid(self, form):
        if form.is_valid():
            if form.get_user().is_active:
                login(self.request, form.get_user())
                self.request.session["userfromdomain"] = form.userfromdomain
                if hasattr(self.request.user, "persona"):
                    pc = self.request.user.persona.personaconfiguracion
                    pc.bloqueado = False
                    pc.save()
                #
                Token.objects.filter(user=self.request.user).delete()
                Token.objects.create(user=self.request.user)
                #
                context = self.get_context_data(**self.get_form_kwargs())
                self.template_name = "inicio/login/ok.html"
                context["newurl"] = reverse("appini:inicio")  # self.get_success_url()
                return self.render_to_response(context=context)
            else:
                form.add_error(None, _("This account is inactive."))
        return super(InicioLogin, self).form_valid(form)


class InicioLogout(LogoutView):
    next_page = reverse_lazy("appini:inicio_login")

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, "persona"):
            pc = request.user.persona.personaconfiguracion
            pc.bloqueado = False
            pc.save()
        _result = super(InicioLogout, self).dispatch(request, *args, **kwargs)
        if request.session.get("bloqueo"):
            del request.session["bloqueo"]
        if request.session.get("usrses"):
            del request.session["usrses"]
        if request.session.get("desbloqueo"):
            del request.session["desbloqueo"]
        if request.session.get("userfromdomain"):
            del request.session["userfromdomain"]
        return _result


class InicioChangePassword(TemplateValidaLogin, PasswordChangeView):
    template_name = "inicio/changepassword/vista.html"
    form_class = FormChangePassword
    success_url = reverse_lazy("appini:inicio_cambiar_password")

    def get_form(self, form_class=None):
        form = super(InicioChangePassword, self).get_form(form_class)
        if self.request.user.is_superuser or self.request.user.persona.personaconfiguracion.cambiarpassword:
            form.fields["old_password"].required = True
            form.fields["new_password1"].required = True
            form.fields["new_password2"].required = True
        return form

    def get_context_data(self, **kwargs):
        context = super(InicioChangePassword, self).get_context_data(**kwargs)
        if self.request.user.is_superuser or self.request.user.persona.personaconfiguracion.cambiarpassword:
            context["noBotonCancelar"] = True
        return context

    def form_valid(self, form):
        _result = super().form_valid(form)
        if not self.request.user.is_superuser:
            perconf = self.request.user.persona.personaconfiguracion
            perconf.cambiarpassword = False
            perconf.save()
        context = self.get_context_data(**self.get_form_kwargs())
        context["esok"] = True
        context["noBotonGuardar"] = True
        context["botoncancelartexto"] = "Aceptar"
        return self.render_to_response(context)


class InicioResetPassword(TemplateConfig, PasswordResetView):
    template_name = "inicio/resetpassword/vista.html"
    extra_email_context = {
        "configapp": settings.CONFIG_APP
    }
    success_url = reverse_lazy('appini:inicio_reset_password_done')
    form_class = InicioResetPasswordForm
    subject_template_name = "inicio/resetpassword/correo_asunto.html"
    html_email_template_name = "inicio/resetpassword/correo_cuerpo.html"
    email_template_name = "inicio/resetpassword/correo_cuerpo.html"

    def form_valid(self, form):
        # Buscamos el email en la BD
        if User.objects.filter(email=form.cleaned_data["email"]).exists():
            return super(InicioResetPassword, self).form_valid(form)
        else:
            self.template_name = "inicio/resetpassword/formulario.html"
            form.add_error(None, "El correo no está registrado")
            return self.render_to_response(self.get_context_data(form=form))


class InicioResetPasswordDone(TemplateConfig, PasswordResetDoneView):
    template_name = "inicio/resetpassword/done.html"


class InicioResetPasswordConfirm(TemplateConfig, PasswordResetConfirmView):
    template_name = "inicio/resetpassword/confirm.html"
    success_url = reverse_lazy('appini:inicio_reset_password_confirm_ok')
    form_class = InicioResetPasswordConfirmForm

    def get_context_data(self, **kwargs):
        context = super(InicioResetPasswordConfirm, self).get_context_data(**kwargs)
        context["usuario"] = self.user
        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.POST:
            self.template_name = "inicio/resetpassword/confirm_form.html"
        return super(InicioResetPasswordConfirm, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        frmval = super(InicioResetPasswordConfirm, self).form_valid(form)
        self.request.session["recovery_confirmado_pk"] = self.user.pk
        CerrarSesion(self.user.pk)
        return frmval


class InicioResetPasswordConfirmOk(TemplateConfig, PasswordResetCompleteView):
    template_name = 'inicio/resetpassword/confirm_ok.html'

    def get_context_data(self, **kwargs):
        context = super(InicioResetPasswordConfirmOk, self).get_context_data(**kwargs)
        if self.request.session.get("recovery_confirmado_pk"):
            context["usuario"] = User.objects.filter(pk=self.request.session["recovery_confirmado_pk"]).first()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.session.get("recovery_confirmado_pk"):
            del self.request.session["recovery_confirmado_pk"]
            return super(InicioResetPasswordConfirmOk, self).render_to_response(context, **response_kwargs)
        else:
            return HttpResponseRedirect(reverse("appini:inicio_reset_password"))


class InicioResetPasswordPrevio(TemplateConfig, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        context["user"] = User.objects.get(username="43279483")
        context["token"] = 'abc'
        context["uid"] = 'xyz'
        body = loader.render_to_string("inicio/resetpassword/correo_cuerpo.html", context)
        return HttpResponse(body)


class InicioInfo(TemplateConfig, TemplateView):
    template_name = "inicio/info/vista.html"


class AreaChange(TemplateValidaLogin, FormView):
    template_name = "inicio/changearea/vista.html"
    form_class = AreaChangeForm

    def get_context_data(self, **kwargs):
        context = super(AreaChange, self).get_context_data(**kwargs)
        if self.request.method == "GET":
            pta = self.request.session.get("cambioperiodo", self.request.user.persona.ultimoperiodotrabajo.pk)
            ptaArea = PeriodoTrabajo.objects.get(pk=pta).area
            if self.request.user.persona.TrabajosActivos(
                    self.request.session.get("cambioperiodo")
            ).exclude(
                area=ptaArea
            ).count() > 0:
                context["cambiar"] = True
        return context

    def get_form(self, form_class=None):
        form = super(AreaChange, self).get_form(form_class)
        form.fields["areanueva"].queryset = self.request.user.persona.TrabajosActivos(
            self.request.session.get("cambioperiodo")
        )
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            areanueva = form.cleaned_data["areanueva"].pk
            if areanueva == self.request.user.persona.ultimoperiodotrabajo.pk:
                if self.request.session.get("cambioperiodo"):
                    del self.request.session["cambioperiodo"]
            else:
                if self.request.session.get("cambioperiodo"):
                    del self.request.session["cambioperiodo"]
                self.request.session["cambioperiodo"] = areanueva
            self.request.session.modified = True
            context["cambiook"] = True
        return self.render_to_response(context)


class AreaChangeListar(AutoResponseView):
    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        resultados = []
        listas = ((False, "Unidades Organizacionales"), (True, "Comisiones"))
        for lista in listas:
            hijos = []
            for idx, obj in enumerate(self.object_list.filter(area__paracomisiones=lista[0])):
                hijos.append({
                    'text': self.widget.label_from_instance(obj),
                    'id': obj.pk,
                })
            if len(hijos) > 0:
                resultados.append({
                    "text": lista[1],
                    "children": hijos
                })
        return JsonResponse({
            'results': resultados,
            'more': context['page_obj'].has_next()
        })


def CerrarSesion(userid):
    user = User.objects.filter(pk=userid).first()
    if user:
        from apps.sockets.vistas.mensajes import SocketMsg
        # Borramos todas las Sesiones
        [s.delete() for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == str(user.id)]
        # Mandamos un mensaje a todas las sesiones para actualizar la página
        SocketMsg(
            userid=user.id,
            funcpost="reloadPage()"
        )
