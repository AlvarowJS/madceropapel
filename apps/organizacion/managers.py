"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Q, Case, When, F, Value
from django.db.models.functions import Concat, Upper
from django.utils import timezone
from pytz import timezone as pytz_timezone

from modulos.utiles.clases.formularios import AuditoriaManager


class AMPeriodoTrabajo(AuditoriaManager):
    def get_queryset(self):
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        return super(AMPeriodoTrabajo, self).get_queryset().annotate(
            areacondep=Concat(
                Upper(F("area__dependencia__nombrecorto")),
                Value(" - "),
                F("area__nombre")
            ),
            cargonombre=Case(
                When(persona__sexo="F", then=F("cargo__nombref")),
                default=F("cargo__nombrem")
            ),
            encargaturaestado=Case(
                When(
                    tipo="EN",
                    then=Case(
                        When(
                            Q(fin__gte=fechaActual, encargaturaplantilla__isnull=True),
                            then=Value("Por autorizar")
                        ),
                        When(
                            Q(inicio__gte=fechaActual, encargaturaplantilla__isnull=False,
                              encargaturaplantillaanulacion__isnull=True),
                            then=Value("Autorizado - Por iniciar")
                        ),
                        When(
                            Q(
                                inicio__lte=fechaActual, fin__gte=fechaActual, encargaturaplantilla__isnull=False,
                                encargaturaplantillaanulacion__isnull=True
                            ),
                            then=Value("Autorizado")
                        ),
                        When(
                            Q(
                                encargaturaplantillaanulacion__isnull=False
                            ),
                            then=Value("Anulado")
                        ),
                        When(
                            Q(
                                fin__lt=fechaActual, encargaturaplantilla__isnull=True
                            ),
                            then=Value("Vencido")
                        ),
                        default=Value("Terminado")
                    )
                ),
                When(
                    tipo="EP",
                    then=Case(
                        When(
                            Q(fin__gte=fechaActual) | Q(fin__isnull=True),
                            then=Value("Activo")
                        ),
                        default=Value("Inactivo")
                    )
                ),
                When(
                    tipo="AP",
                    then=Case(
                        When(
                            Q(fin__gte=fechaActual, aprobador__isnull=True),
                            then=Value("Por autorizar")
                        ),
                        When(
                            Q(inicio__gte=fechaActual, aprobador__isnull=False),
                            then=Value("Autorizado - Por Iniciar")
                        ),
                        When(
                            Q(inicio__lte=fechaActual, fin__gte=fechaActual, aprobador__isnull=False),
                            then=Value("Autorizado")
                        ),
                        When(
                            Q(fin__lt=fechaActual,aprobador__isnull=True),
                            then=Value("Vencido")
                        ),
                        default=Value("Terminado")
                    )
                ),
                default=Value("")
            )
        )


class AMTrabajadoresActuales(AMPeriodoTrabajo):
    def get_queryset(self):
        # fechaActual = timezone.localdate(timezone.now())
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        _result = super(AMTrabajadoresActuales, self).get_queryset().filter(
            inicio__lte=fechaActual,
            activo=True
        ).filter(
            Q(fin__isnull=True)
            |
            Q(fin__gte=fechaActual)
        ).filter(
            Q(tipo="NN")
            |
            Q(tipo="EN", encargaturaplantilla__isnull=False, encargaturaplantillaanulacion__isnull=True)
            |
            Q(tipo="EP")
            |
            Q(tipo="AP", aprobador__isnull=False)
        )
        # for reg in _result:
        #     if reg.id == 901:
        #         print("Reg", reg.inicio, fechahoraActual)
        return _result


class AMAreaNormal(AuditoriaManager):
    pass


class AMArea(AuditoriaManager):
    def get_queryset(self):
        return super(AMArea, self).get_queryset().annotate(
            comisionestado=Case(
                When(
                    paracomisiones=True,
                    then=Case(
                        When(
                            Q(documentoautorizacion__isnull=True, activo=False),
                            then=Value("Pendiente de Firma")
                        ),
                        default=Value("Autorizado")
                    )
                ),
                default=Value("")
            )
        )
