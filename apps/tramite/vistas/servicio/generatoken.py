"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.compat import coreapi, coreschema
from rest_framework.authtoken.models import Token
from pytz import timezone as pytz_timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema


def expires_in(token):
    expiracion = 60 * 30  # 30 minutos
    time_elapsed = timezone.now() - token.created  # .astimezone(pytz_timezone(settings.TIME_ZONE))
    left_time = timedelta(seconds=expiracion) - time_elapsed
    return left_time


def is_token_expired(token):
    return expires_in(token) < timedelta(seconds=0)


def token_expire_handler(token):
    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
        token = Token.objects.create(user=token.user)
    return is_expired, token


class AuthTokenSerializer(serializers.Serializer):
    User = serializers.CharField(label=_("Username"))
    Pwd = serializers.CharField(
        label=_("Password", ),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs.get('User')
        password = attrs.get('Pwd')
        user = None
        msg = None
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username, password=password
            )
            if not user:
                msg = _('Unable to log in with provided credentials.')
                # raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            # raise serializers.ValidationError(msg, code='authorization')
        attrs['msg'] = msg
        attrs['user'] = user
        return attrs


class SeguridadAutenticacion(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    if coreapi is not None and coreschema is not None:
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="User",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="User",
                        description="Valid username for authentication",
                    ),
                ),
                coreapi.Field(
                    name="Pwd",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),
            ],
            encoding="application/json",
        )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=False)
        user = serializer.validated_data.get('user', None)
        ok = False
        key = msg = expira = ""
        if user:
            ok = True
            token, created = Token.objects.get_or_create(user=user)
            is_expired, token = token_expire_handler(token)
            key = token.key
            expira = (
                    timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE)) +
                    expires_in(token)
            ).strftime("%d/%m/%Y %H:%M")
        else:
            msg = serializer.validated_data.get('msg', "")
        return Response({
            'ok': ok,
            'message': msg,
            'token': key,
            'tokenexpiration': expira
        })
