"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import F, Value, CharField, Case, When, Subquery, OuterRef, Q, DateTimeField
from django.db.models.functions import Concat, LPad, Cast, StrIndex, Substr

from modulos.utiles.clases.formularios import AuditoriaManager


class AMDistribuidor(AuditoriaManager):
    def get_queryset(self):
        return super(AMDistribuidor, self).get_queryset().annotate(
            documentotipo=Case(
                When(tipo="C", then=Value("RUC")),
                default=F("persona__tipodocumentoidentidad__codigo")
            ),
            documentonumero=Case(
                When(tipo="C", then=F("personajuridica__ruc")),
                default=F("persona__numero")
            ),
            nombre=Case(
                When(
                    tipo="C",
                    then=Case(
                        When(personajuridica__nombrecomercial__isnull=True, then=F("personajuridica__razonsocial")),
                        default=F("personajuridica__nombrecomercial")
                    )
                ),
                When(
                    tipo="M",
                    then=F("persona__apellidocompleto")
                )
            )
        )


def am_expediente_nro(modelo):
    if len(modelo) > 0:
        modelo += "__"
    return Concat(
        F(modelo + "dependencia__codigo"),
        Value("-"),
        F(modelo + "anio"),
        Value("-"),
        LPad(
            Cast(
                modelo + "numero",
                output_field=CharField()
            ),
            settings.CONFIG_APP["ExpedienteZero"],
            Value("0")
        ),
        output_field=CharField()
    )


def am_documento_nro(modelo, mini=False):
    if len(modelo) > 0:
        modelo += "__"
    modomini = "nombre" if not mini else "nombrecorto"
    return eval(
        'Concat(' +
        '   F("' + modelo + 'documentotipoarea__documentotipo__' + modomini + '"),' +
        '   Case(' +
        '       When(Q(' + modelo + 'numero__isnull=True) | Q(' + modelo + 'numero=0), then=Value(" s/n ")), ' +
        '       default=Concat(' +
        '           Value(" N° "),' +
        '           Case(' +
        '               When(' + modelo + 'origentipo__in=["O", "P"], ' +
        '                   then=Value(settings.CONFIG_APP["DocumentoPreposDigital"])' +
        '               ),' +
        '               default=Value("")' +
        '           ),' +
        '           Cast(' +
        '               "' + modelo + 'numero",' +
        '               output_field=CharField()' +
        '           ),' +
        '       )' +
        '   )' +
        ')'
    )


def am_documento_siglas(modelo, mini=False):
    if len(modelo) > 0:
        modelo += "__"
    modomini = "" if not mini else "mini"
    return eval(
        'Concat(' +
        '   F("documentonro' + modomini + '"), ' +
        '   Case(' +
        '       When(Q(' + modelo + 'origentipo__in=["O", "P"], ' + modelo + 'numero__isnull=False),' +
        '           then=Concat(' +
        '               Value("-"),' +
        '               Cast("' + modelo + 'anio", CharField())' +
        '           )' +
        '       ), default=Value("")' +
        '   ),' +
        '   Case(' +
        '       When(' +
        '           Q(' + modelo + 'siglas__isnull=True) | ' +
        '           Q(' + modelo + 'siglas__exact="") | ' +
        '           Q(' + modelo + 'siglas__startswith="-"), ' +
        '           then=Value("")' +
        '       ), ' +
        '       When(' + modelo + 'origentipo__in=["O", "P"], then=Value("")), ' +
        '       default=Value("-") ' +
        '   ), ' +
        '   F("' + modelo + 'siglas") ' +
        ')'
    )


def am_remitente(documento):
    a = (
            'Case(' +
            '    When(' +
            '       ' + documento + '__origentipo__in=["O", "P"],' +
            '       then=Concat(' +
            '           F("' + documento + '__responsable__area__nombrecorto"), ' +
            '           Value(" - "), ' +
            '           Case(' +
            '               When(posnombres__gt=0, then=Substr("' + documento + '__responsable__persona__nombres", 1, ' +
            '               F("posnombres") - 1)), ' +
            '               default=F("' + documento + '__responsable__persona__nombres")' +
            '           ),' +
            '           Value(" "),' +
            '           F("' + documento + '__responsable__persona__paterno")' +
            '       )' +
            '    ),' +
            '    default=Case(' +
            '       When(' +
            '           ' + documento + '__remitentetipo__in=["C"],' +
            '           then=Concat(' +
            '               F("' + documento + '__ciudadanoemisor__numero"),' +
            '               Value(" - "),' +
            '               F("' + documento + '__ciudadanoemisor__apellidocompleto")' +
            '           )' +
            '       ),' +
            '       When(' +
            '           ' + documento + '__remitentetipo__in=["J"],' +
            '           then=Concat(' +
            '               F("' + documento + '__personajuridica__ruc"),' +
            '               Value(" - "),' +
            '               Case(' +
            '                   When(' +
            '                       ' + documento + '__personajuridica__nombrecomercial__isnull=True, ' +
            '                       then=F("' + documento + '__personajuridica__razonsocial") ' +
            '                   ),' +
            '                   default=F("' + documento + '__personajuridica__nombrecomercial")' +
            '               )' +
            '           )' +
            '       ),' +
            '       default=Value("")' +
            '    )' +
            ')'
    )
    return eval(a)


def am_destinatario(destino=""):
    if len(destino) > 0:
        destino += "__"
    result = (
            'Case( ' +
            '    When(' +
            '        ' + destino + 'tipodestinatario="UO", ' +
            '        then=Concat( ' +
            '            F("' + destino + 'periodotrabajo__area__nombrecorto"), ' +
            '            Value(" - "), ' +
            '            F("' + destino + 'periodotrabajo__persona__apellidocompleto") ' +
            '        )' +
            '    ), ' +
            '    When(' +
            '        ' + destino + 'tipodestinatario="PJ", ' +
            '        then=Concat(' +
            '            F("' + destino + 'personajuridica__ruc"),' +
            '            Value(" - "),' +
            '            Case(' +
            '                When(' +
            '                    ' + destino + 'personajuridica__nombrecomercial__isnull=True, ' +
            '                    then=F("' + destino + 'personajuridica__razonsocial")' +
            '                ),' +
            '                default=F("' + destino + 'personajuridica__nombrecomercial")' +
            '            ),' +
            '            Case(' +
            '                When(' + destino + 'persona__isnull=True, then=Value("")),' +
            '                default=Concat(' +
            '                    Value(" - "),' +
            '                    F("' + destino + 'persona__apellidocompleto")' +
            '                )' +
            '            )' +
            '        )' +
            '    ),' +
            '    When(' +
            '        ' + destino + 'tipodestinatario="CI",' +
            '        then=Concat(' +
            '            F("' + destino + 'persona__numero"),' +
            '            Value(" - "),' +
            '            F("' + destino + 'persona__apellidocompleto")' +
            '        )' +
            '    ),' +
            '    default=Value("")' +
            ')'
    )

    return eval(result)


class AMExpediente(AuditoriaManager):
    def get_queryset(self):
        return super(AMExpediente, self).get_queryset().annotate(
            expedientenro=am_expediente_nro("")
        )


class AMDocumentoClean(AuditoriaManager):
    def get_queryset(self):
        return super(AMDocumentoClean, self).get_queryset()


class AMDocumento(AuditoriaManager):
    def get_queryset(self):
        return super(AMDocumento, self).get_queryset().annotate(
            expedientenro=am_expediente_nro("expediente"),
            documentonro=am_documento_nro(""),
            documentonromini=am_documento_nro("", True),
            remitente=Case(
                When(
                    origentipo__in=["O", "P"],
                    then=Concat(
                        F("responsable__area__nombrecorto"),
                        Value(" - "),
                        F("responsable__persona__apellidocompleto")
                    )
                ),
                default=Case(
                    When(
                        remitentetipo="C",
                        then=Concat(
                            Case(
                                When(ciudadanoemisor__tipodocumentoidentidad__codigo="OTR", then=Value("")),
                                default=Concat(
                                    F("ciudadanoemisor__numero"),
                                    Value(" - "),
                                )
                            ),
                            F("ciudadanoemisor__apellidocompleto")
                        )
                    ),
                    default=Case(
                        When(
                            personajuridica__tipo="R",
                            then=Concat(
                                F("personajuridica__ruc"),
                                Value(" - "),
                                Case(
                                    When(personajuridica__nombrecomercial__isnull=True,
                                         then=F("personajuridica__razonsocial")),
                                    default=F("personajuridica__nombrecomercial")
                                )
                            )
                        ),
                        default=F("personajuridica__razonsocial")
                    )
                )
            )
        ).annotate(
            documentonrosiglas=am_documento_siglas(""),
            documentonrosiglasmini=am_documento_siglas("", True)
        )


class AMDestino(AuditoriaManager):
    def get_queryset(self):
        from apps.tramite.models import DestinoEstado
        return super(AMDestino, self).get_queryset().annotate(
            documentonro=am_documento_nro("documento"),
            expedientenro=am_expediente_nro("documento__expediente"),
            documentonrosiglas=am_documento_siglas("documento"),
            posnombres=StrIndex("documento__responsable__persona__nombres", Value(" ")),
            remitente=am_remitente("documento"),
            destinatario=am_destinatario(),
            ubigeofull=Case(
                When(
                    ubigeo__isnull=False,
                    then=Concat(
                        F("ubigeo__provincia__departamento__nombre"),
                        Value(" / "),
                        F("ubigeo__provincia__nombre"),
                        Value(" / "),
                        F("ubigeo__nombre")
                    )
                ),
                default=Value("")
            ),
            ultimorechazo=Subquery(DestinoEstado.objects.filter(
                estado="RH", destino__pk=OuterRef("pk")
            ).order_by("-creado").values("pk")[:1]),
            destinoemision=Case(
                When(ultimorechazo__isnull=True, then=F("documento__estadoemitido__creado")),
                default=Subquery(DestinoEstado.objects.filter(
                    estado="NL", destino__pk=OuterRef("pk"), pk__gt=OuterRef("ultimorechazo")
                ).order_by("creado").values("creado")[:1]),
                output_field=DateTimeField()
            ),
            ultimoestadomensajeriae=Case(
                When(ultimoestadomensajeria__isnull=True, then=Value("")),
                default=F("ultimoestadomensajeria__estado")
            )
        )


class AMDocumentoFirma(AuditoriaManager):
    def get_queryset(self):
        return super(AMDocumentoFirma, self).get_queryset().annotate(
            expedientenro=am_expediente_nro("documento__expediente"),
            documentonro=am_documento_nro("documento")
        )


class AMAnexoFirma(AuditoriaManager):
    def get_queryset(self):
        return super(AMAnexoFirma, self).get_queryset().annotate(
            expedientenro=am_expediente_nro("anexo__documento__expediente"),
            documentonro=am_documento_nro("anexo__documento")
        )


class AMCargoExternoDetalle(AuditoriaManager):
    def get_queryset(self):
        return super(AMCargoExternoDetalle, self).get_queryset().annotate(
            expedientenro=am_expediente_nro("destino__documento__expediente"),
            documentonro=am_documento_nro("destino__documento"),
            posnombres=StrIndex("destino__documento__responsable__persona__nombres", Value(" ")),
            remitente=am_remitente("destino__documento"),
            destinatario=am_destinatario("destino"),
            ubigeonombre=Case(
                When(destino__ubigeo__isnull=True, then=Value("-")),
                default=Concat(
                    F("destino__ubigeo__provincia__departamento__nombre"),
                    Value(" / "),
                    F("destino__ubigeo__provincia__nombre"),
                    Value(" / "),
                    F("destino__ubigeo__nombre")
                )
            ),
            ubigeonombrenew=Case(
                When(ubigeo__isnull=True, then=Value(None)),
                default=Concat(
                    F("ubigeo__provincia__departamento__nombre"),
                    Value(" / "),
                    F("ubigeo__provincia__nombre"),
                    Value(" / "),
                    F("ubigeo__nombre")
                )
            ),
            direccionfull=Concat(
                F("destino__direccion"),
                Case(
                    When(destino__referencia__isnull=True, then=Value("")),
                    default=Concat(Value(" - "), F("destino__referencia"))
                )
            ),
            direccionfullnew=Case(
                When(direccion__isnull=True, then=Value(None)),
                default=Concat(
                    F("direccion"),
                    Case(
                        When(referencia__isnull=True, then=Value("")),
                        default=Concat(Value(" - "), F("referencia"))
                    )
                )
            )
        )
