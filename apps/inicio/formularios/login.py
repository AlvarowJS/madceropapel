"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import AuthenticationForm, UsernameField, PasswordChangeForm, PasswordResetForm, \
    SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template import loader
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ldap3 import Server, Connection

from apps.organizacion.models import PeriodoTrabajo
from modulos.utiles.clases.campos import AppInputTextWidget, AppInputText
from modulos.utiles.clases.correo import CorreoEnviar
from modulos.utiles.clases.formularios import AppBaseForm


class InicioLoginForm(AppBaseForm, AuthenticationForm):
    username = UsernameField(
        widget=AppInputTextWidget(
            label=_("User"),
            iconprepend="flaticon2-user",
            flotante=True
        )
    )
    password = AppInputText(
        label=_("Password"),
        strip=False,
        password=True,
        iconprepend="fas fa-key",
        flotante=True
    )
    firstfield = "username"
    userfromdomain = False

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username is not None and password:
            emp = PeriodoTrabajo.objects.filter(
                Q(persona__usuario__username=username)
                |
                Q(persona__personaconfiguracion__usuariodominio=username)
            ).first()
            self.userfromdomain = False
            if emp:
                user = User.objects.filter(username=username).first()
                # Si no existe el usuario verificamos si existe en Active Directory
                if not user and settings.CONFIG_APP["LDAP"]["STATUS"]:
                    domain = "ldap://" + '.'.join([
                        settings.CONFIG_APP["LDAP"]["DOMAIN"],
                        settings.CONFIG_APP["LDAP"]["DC1"],
                        settings.CONFIG_APP["LDAP"]["DC2"]
                    ])
                    oServer = Server(
                        domain,
                        use_ssl=settings.CONFIG_APP["LDAP"]["SSL"],
                        port=settings.CONFIG_APP["LDAP"]["PORT"]
                    )
                    oUser = "%s\%s" % (
                        settings.CONFIG_APP["LDAP"]["DOMAIN"],
                        username
                    )
                    try:
                        Connection(oServer, user=oUser, password=password, read_only=True, auto_bind=True)
                        user = User.objects.filter(persona__personaconfiguracion__usuariodominio=username).first()
                        self.userfromdomain = True
                    except Exception as e:
                        raise self.get_invalid_login_error()
                if user:
                    is_active = True if user is None else user.is_active
                    if is_active:
                        usorestante = (settings.CONFIG_APP["FechaInicio"] - timezone.now()).total_seconds()
                        if usorestante < 0 or user.is_superuser or user.is_staff:
                            if self.userfromdomain:
                                self.user_cache = user
                            else:
                                self.user_cache = authenticate(self.request, username=username, password=password)
                        else:
                            raise ValidationError(
                                "<div class='text-center'>Ud. puede ingresar al Módulo a partir del <br> %s</div>" % (
                                    settings.CONFIG_APP["FechaInicio"].strftime("%d/%m/%Y %H:%M %p")
                                ),
                                code='invalid_login',
                                params={'username': self.username_field.verbose_name},
                            )
                        if self.user_cache is None:
                            raise self.get_invalid_login_error()
                    else:
                        self.confirm_login_allowed(user)
                else:
                    raise self.get_invalid_login_error()
            else:
                user = User.objects.filter(username=username).first()
                if user and user.is_superuser:
                    self.user_cache = authenticate(self.request, username=username, password=password)
                    if self.user_cache is None:
                        raise self.get_invalid_login_error()
                else:
                    raise self.get_invalid_login_error()
            if user:
                if not user.is_superuser and not user.persona.periodotrabajoactual():
                    raise ValidationError(
                        "Ud. no tiene acceso",
                        code="invalid_login",
                        params={"username": self.username_field.verbose_name},
                    )
        return self.cleaned_data


class FormChangePassword(AppBaseForm, PasswordChangeForm):
    firstfield = "old_password"


class InicioResetPasswordForm(AppBaseForm, PasswordResetForm):
    email = UsernameField(
        widget=AppInputTextWidget(
            label=_("Email"),
            iconprepend="flaticon2-mail",
            flotante=True
        )
    )
    firstfield = "email"

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        ce = CorreoEnviar(to_email, subject, body)
        ce.enviar()


class InicioResetPasswordConfirmForm(AppBaseForm, SetPasswordForm):
    new_password1 = AppInputText(
        label=_("New password"),
        # widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        password=True,
        iconprepend="fas fa-key",
        flotante=True,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = AppInputText(
        label=_("New password confirmation"),
        strip=False,
        # widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        password=True,
        iconprepend="fas fa-key",
        flotante=True,
    )
    firstfield = "new_password1"
