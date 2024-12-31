"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Case, When, Value, F
from django.db.models.functions import Concat, StrIndex, Substr

from modulos.utiles.clases.formularios import AuditoriaManager

from threading import local

_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


class AMPersona(AuditoriaManager):
    def get_queryset(self):
        return super(AMPersona, self).get_queryset().annotate(
            posnombres=StrIndex("nombres", Value(" ")),
            nombrecorto=Concat(
                Case(
                    When(posnombres__gt=0, then=Substr("nombres", 1, F("posnombres") - 1)),
                    default=F("nombres")
                ),
                Value(" "),
                F("paterno")
            )
        )


class AMPersonaJuridica(AuditoriaManager):
    def get_queryset(self):
        return super(AMPersonaJuridica, self).get_queryset().annotate(
            razoncomercial=Case(
                When(nombrecomercial__isnull=True, then=F("razonsocial")),
                default=F("nombrecomercial")
            )
        )
