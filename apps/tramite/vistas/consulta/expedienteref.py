"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json

import requests
from django.conf import settings
from django.db.models import F, Value, CharField, Case, When, Q
from django.db.models.functions import Concat, ExtractDay, ExtractMonth, ExtractYear, LPad, Cast
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.inicio.vistas.nucleo import ObtenerTokenNucleo
from apps.organizacion.models import Dependencia, DocumentoTipoArea
from apps.tramite.models import Expediente, DocumentoReferenciaOrigen, DocumentoReferenciaModo, Documento


class ConsultaExpedienteRef(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/expedienteref.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        data = request.POST
        context["expediente"], context["mensaje"], context["origen"] = ConsultarExpediente(data, request)
        context["ctrlnro"] = data["ctrlnro"]
        context["ctrlemi"] = data["ctrlemi"]
        context["ctrldes"] = data["ctrldes"]
        return self.render_to_response(context=context)


def ConsultarExpediente(data, request):
    periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
    _expediente = None
    _mensaje = "No se pudo obtener los datos del expediente"
    # PARAMETROS ================================================
    # ORIGEN
    origen = data.get("origen")
    if not isinstance(origen, DocumentoReferenciaOrigen):
        origen = DocumentoReferenciaOrigen.objects.get(pk=origen)
    # MODO
    modo = data.get("modoref")
    if not isinstance(modo, DocumentoReferenciaModo):
        modo = DocumentoReferenciaModo.objects.get(pk=modo)
    # AÑO
    anio = data.get("anio")
    # NUMERO
    numero = str(data.get("numero", "0"))
    if numero == "":
        numero = "0"
    numero = int(numero)
    # DEPENDENCIA
    depid = data.get("dependencia")
    if depid:
        depid = int(depid if isinstance(depid, str) else depid.pk)
    else:
        depid = Dependencia.objects.get(codigo=settings.CONFIG_APP["Dependencia"]).pk
    # OFICINA y TIPO DE DOCUMENTO
    if origen.codigo == "MCP":
        if modo.codigo == "D":
            ofiid = data.get("oficinamcp", "0")
            ofiid = int(ofiid or "0") if isinstance(ofiid, str) else ofiid.pk
            # TIPO DE DOCUMENTO
            tipodoc = data.get("documentotipomcp", "0")
            tipodoc = int(tipodoc or "0") if isinstance(tipodoc, str) else tipodoc.codigo
            # ORIGEN DEL DOCUMENTO
            origendoc = data.get("documentoorigenmcp", "O")
            origenper = data.get("documentoorigenpermcp", "0")
            if origenper == "":
                origenper = "0"
            origenper = int(origenper)
        else:
            tipodoc = 0
            origendoc = "O"
            origenper = 0
    else:
        ofiid = data.get("oficinasgd", "0")
        ofiid = ofiid if isinstance(ofiid, str) else ofiid.codigo
        # TIPO DE DOCUMENTO
        tipodoc = data.get("documentotiposgd", "0")
        tipodoc = tipodoc if isinstance(tipodoc, str) else tipodoc.codigo
        origendoc = ""
        origenper = 0
    #
    # ===========================================================
    if origen.codigo in ["SGD", "MAD"]:
        _expurl = settings.CONFIG_APP["NUCLEO"][origen.codigo]["externo"]
        if origen.codigo == "SGD":
            if modo.codigo == "E":
                _numero = "{0}-{1:0>7}".format(str(anio), str(numero))
                _expurl = _expurl.format(anio=anio, numero=numero)
            elif modo.codigo == "O":
                _expurl = settings.CONFIG_APP["NUCLEO"][origen.codigo]["interno"]
                _expurl = _expurl.format(area=ofiid, anio=anio, numero=numero)
            elif modo.codigo == "D":
                _expurl = settings.CONFIG_APP["NUCLEO"][origen.codigo]["documento"]
                _expurl = _expurl.format(area=ofiid, tipodoc=tipodoc, anio=anio, numero=numero)
        else:
            _numero = "{0:0>8}".format(str(numero))
            _expurl = _expurl % numero
        # === CONSULTA
        urlnucleo = settings.CONFIG_APP["NUCLEO"]["URL"]
        try:
            token = ObtenerTokenNucleo()
            r = requests.post(
                urlnucleo + _expurl,
                headers={
                    "Authorization": "Token " + token
                }
            )
            if r.ok:
                result = json.loads(r.text)
                if result["success"]:
                    _expediente = result["expediente"]
                else:
                    _mensaje = "Expediente %s no encontrado" % origen.siglas
        except Exception as e:
            pass
    else:
        if modo.codigo == "E":
            expediente = Expediente.objects.filter(
                dependencia_id=depid,
                anio=anio,
                numero=numero
            ).first()
            if expediente:
                if expediente.documentos.count() > 0:
                    if expediente.documentos.order_by("creado").first().ultimoestado.estado in \
                            ["EM", "AT", "RP", "RT", "TR", "AR"]:
                        documentos = expediente.documentos.annotate(
                            remitente=Case(
                                When(
                                    origentipo="O",
                                    then=Concat(
                                        F("responsable__area__nombre"),
                                        Value(" - "),
                                        F("responsable__persona__apellidocompleto")
                                    )
                                ),
                                When(
                                    origentipo="P",
                                    then=Concat(
                                        F("responsable__area__nombre"),
                                        Value(" - "),
                                        F("responsable__persona__apellidocompleto")
                                    )
                                ),
                                default=Concat(
                                    Case(
                                        When(
                                            remitentetipo="J",
                                            then=Case(
                                                When(
                                                    personajuridica__nombrecomercial__isnull=True,
                                                    then=F("personajuridica__razonsocial")
                                                ),
                                                default=F("personajuridica__nombrecomercial")
                                            )
                                        ),
                                        default=Value("")
                                    ),
                                    Case(
                                        When(
                                            Q(remitentetipo="J", ciudadanoemisor__isnull=False),
                                            then=Value(" - ")
                                        ),
                                        default=Value("")
                                    ),
                                    Case(
                                        When(
                                            ciudadanoemisor__isnull=False,
                                            then=F("ciudadanoemisor__apellidocompleto")
                                        ),
                                        default=Value("")
                                    ),
                                )
                            ),
                            fechadocumento=Concat(
                                LPad(Cast(ExtractDay("fecha"), CharField()), 2, Value("0")),
                                Value("/"),
                                LPad(Cast(ExtractMonth("fecha"), CharField()), 2, Value("0")),
                                Value("/"),
                                Cast(ExtractYear("fecha"), CharField()),
                                output_field=CharField()
                            ),
                            firmatitulo=Case(
                                When(
                                    responsable__isnull=True,
                                    then=Value("Emitido")
                                ),
                                default=Value("Firmado")
                            ),
                            firma=Case(
                                When(
                                    responsable__isnull=True,
                                    then=F("emisor__persona__nombrecompleto"),
                                ),
                                default=F("responsable__persona__nombrecompleto")
                            ),
                            cargo=Case(
                                When(
                                    responsable__isnull=True,
                                    then=Case(
                                        When(emisor__persona__sexo="F", then=F("emisor__cargo__nombref")),
                                        default=F("emisor__cargo__nombrem")
                                    )
                                ),
                                default=Case(
                                    When(responsable__persona__sexo="F", then=F("responsable__cargo__nombref")),
                                    default=F("responsable__cargo__nombrem")
                                )
                            ),
                            nuemi=Value("0"),
                            oficina=Case(
                                When(
                                    responsable__isnull=True,
                                    then=F("emisor__area__nombrecorto"),
                                ),
                                default=F("responsable__area__nombrecorto")
                            )
                        ).order_by("creado").values(
                            "pk", "remitente", "asunto", "folios", "firma", "cargo", "fechadocumento", "anio",
                            "expedientenro", "nuemi", "firmatitulo", "oficina"
                        )
                        _expediente = documentos[0]
                        _expediente["numdoc"] = Documento.objects.get(pk=_expediente["pk"]).obtenerNumeroSiglas()
                        _mensaje = None
                else:
                    _mensaje = "El expediente no tiene documentos."
        elif modo.codigo == "D":
            documentotipoarea = DocumentoTipoArea.objects.filter(id=tipodoc).first()
            if origendoc == "O":
                origenper = 0
            if documentotipoarea and (
                    origendoc == "O" or (origendoc == "P" and periodoactual.area == documentotipoarea.area)
            ):
                documentos = Documento.objects.annotate(
                    origenper=Value(origenper)
                ).filter(
                    ultimoestado__estado__in=["EM", "AT", "RP", "RT", "TR", "AR"],
                    documentotipoarea_id=tipodoc,
                    responsable__area=documentotipoarea.area,
                    anio=anio,
                    numero=numero,
                    origentipo=origendoc
                ).filter(
                    Q(origenper=0, origentipo="O")
                    |
                    Q(origenper__gt=0, responsable=origenper, origentipo="P")
                ).annotate(
                    remitente=F("responsable__area__nombre"),
                    fechadocumento=Concat(
                        LPad(Cast(ExtractDay("fecha"), CharField()), 2, Value("0")),
                        Value("/"),
                        LPad(Cast(ExtractMonth("fecha"), CharField()), 2, Value("0")),
                        Value("/"),
                        Cast(ExtractYear("fecha"), CharField()),
                        output_field=CharField()
                    ),
                    firmatitulo=Value("Firmado"),
                    oficina=F("responsable__area__nombrecorto"),
                    firma=F("responsable__persona__nombrecompleto"),
                    cargo=Case(
                        When(responsable__persona__sexo="F", then=F("responsable__cargo__nombref")),
                        default=F("responsable__cargo__nombrem")
                    ),
                    nuemi=Cast(F("pk"), output_field=CharField())
                ).order_by("creado").values(
                    "pk", "remitente", "asunto", "folios", "firma", "cargo", "fechadocumento", "anio",
                    "expedientenro", "nuemi", "firmatitulo", "oficina"
                )
                if documentos.count() > 0:
                    _expediente = documentos[0]
                    _expediente["numdoc"] = Documento.objects.get(pk=_expediente["pk"]).obtenerNumeroSiglas()
                    _mensaje = None
    return _expediente, _mensaje, origen
