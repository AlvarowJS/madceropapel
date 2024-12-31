"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Case, When, F, Value, CharField, Count, Q, IntegerField
from django.db.models.functions import Concat, LPad, Cast, Replace
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateConfig
from apps.tramite.models import Documento, Destino, Expediente


class SeguimientoExp(TemplateConfig, TemplateView):
    template_name = "tramite/seguimiento/consulta.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        exp = Expediente.objects.filter(
            anio=self.kwargs.get("anio"),
            numero=self.kwargs.get("num")
        ).first()
        if exp and exp.documentos.count() > 0:
            context["modo"] = "DOC"
            context["documento"] = exp.documentos.order_by("pk").first()
            context["origen"] = request.POST.get("origen")
            context["verdoc"] = (request.POST.get("origen") == "bandeja") or \
                                request.user.persona.ultimoperiodotrabajo.seguimientocompleto
            context["expnro"] = exp.expedientenro
            nodoprim = context["documento"].des_documento.exclude(
                ultimoestado__estado="ANX"
            ).order_by("pk").first()
            if nodoprim:
                context["nodoprimero"] = nodoprim.pk
        return self.render_to_response(context)


class Seguimiento(TemplateConfig, TemplateView):
    template_name = "tramite/seguimiento/consulta.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        modo = self.kwargs.get("modo")
        id = self.kwargs.get("id")
        documento = None
        idsel = id
        if modo == "DOC":
            documento = Documento.objects.filter(pk=id).first()
            idsel = documento.des_documento.exclude(ultimoestado__estado="ANX").order_by("pk").first()
            if idsel:
                idsel = idsel.pk
        elif modo == "DES":
            documento = Documento.objects.exclude(ultimoestado__estado="AN").filter(des_documento__id=id).first()
        context["expnro"] = documento.expedientenro
        context["verdoc"] = (request.POST.get("origen") == "bandeja") or \
                            request.user.persona.ultimoperiodotrabajo.seguimientocompleto
        context["origen"] = request.POST.get("origen")
        context["modo"] = "DOC"
        context["modoreal"] = modo
        context["modoid"] = id
        context["documento"] = documento
        context["nodoprimero"] = idsel
        return self.render_to_response(context)


class SeguimientoNodo(TemplateConfig, TemplateView):
    template_name = "tramite/seguimiento/nodo_lista.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        excanu = request.POST.get("excanu", "ANX")
        expnro = request.POST.get("expnro")
        padre = int(str(request.POST.get("padre")).replace("SEG", ""))
        id = padre
        if padre == 0:
            id = self.kwargs.get("id")
        context["padre"] = padre
        context["destinos"] = ConsultaDocumento(
            request.POST.get("modo"),
            id,
            padre,
            request.POST.get("origen"),
            request.POST.get("modoreal"),
            request.POST.get("modoid"),
            excanu,
            expnro
        )
        if hasattr(request.user, "persona"):
            context["verdoc"] = (request.POST.get("origen") == "bandeja") or \
                                request.user.persona.ultimoperiodotrabajo.seguimientocompleto
        context["nodoprimero"] = request.POST.get("modoid")
        return self.render_to_response(context)


class SeguimientoInfo(TemplateConfig, TemplateView):
    template_name = "tramite/seguimiento/nodo_info.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if hasattr(request.user, "persona"):
            context["verdoc"] = (request.POST.get("origen") == "bandeja") or \
                                request.user.persona.ultimoperiodotrabajo.seguimientocompleto
        destino = Destino.objects.exclude(ultimoestado__estado="ANX")
        destino = destino.filter(pk=self.kwargs.get("id"))
        if context.get("verdoc"):
            destino = destino.annotate(
                urldoc=Case(
                    When(
                        documento__ultimoestado__estado__in=["RE", "AN", "RC", "OF", "PY"],
                        then=Value("")
                    ),
                    default=Replace(
                        Replace(
                            Value(
                                reverse_lazy("apptra:documento_descargar", kwargs={"pk": 0, "cod": 0}),
                                output_field=CharField()
                            ),
                            Value("/0/"),
                            Concat(Value("/"), Cast(F("documento_id"), output_field=CharField()), Value("/"))
                        ),
                        Value("/0"),
                        Concat(Value("/"), Cast(F("pk"), output_field=CharField()))
                    )
                ),
                urldoc2=Case(
                    When(
                        Q(documento__ultimoestado__estado__in=["RE", "AN", "RC", "OF", "PY"])
                        |
                        Q(documento__confidencial=True),
                        then=Value("")
                    ),
                    default=Replace(
                        Value(reverse_lazy("apptra:documento_descargar_fast", kwargs={"pk": 0}),
                              output_field=CharField()),
                        Value("0"),
                        Cast(F("id"), output_field=CharField())
                    )
                )
            )
        destino = destino.first()
        context["destino"] = destino
        if destino.documento.confidencial:
            if destino.documento.creador == request.user or \
                    destino.documento.responsable.persona.usuario == request.user:
                pass
            else:
                context["confidencial"] = True
        return self.render_to_response(context)


def ObtenerRama(destino, expediente, exclusiones):
    if destino:
        _result = [destino.pk]
        if destino.documento.referencias.count() > 0:
            # _result += ObtenerRama(destino.documento.referencias.first().destino, exclusiones)
            for ref in destino.documento.referencias.filter(destino__isnull=False).order_by("pk"):
                if ref.destino.documento.expediente == expediente:
                    _result += ObtenerRama(ref.destino, expediente, exclusiones)
        return _result
    else:
        return []


def ConsultaDocumento(modo, id, padre, origen, modoreal, modoid, excanu="ANX", expedientenro=None):
    data = []
    can = 3 if origen == "general" else 0
    if modo == "DOC" or padre == 0:
        if modo != "DOC" and padre == 0:
            id = Destino.objects.get(pk=id).documento.pk
        documento = Documento.objects.filter(pk=id).first()
        if modo == "DOC" and padre == 0:
            documento = documento.expediente.documentos.order_by("pk").first()
        if modoreal == "DOC":
            destino = Documento.objects.filter(pk=id).first().des_documento.exclude(ultimoestado__estado=excanu).first()
        else:
            destino = Destino.objects.filter(pk=modoid).first()
        data = ConsultaArbol(documento.des_documento.exclude(ultimoestado__estado=excanu), can, None, excanu, documento.expedientenro)
        exclusiones = [dato["id"] for dato in data]
        listarama = ObtenerRama(destino, documento.expediente, exclusiones)
        for idx, destid in enumerate(listarama[:-1]):
            data += ConsultaArbol(
                destinos=Destino.objects.filter(pk=destid).first().documento.des_documento.exclude(
                    ultimoestado__estado=excanu
                ),
                padreid=listarama[idx + 1],
                excanu=excanu,
                expedienteorigen=expedientenro
            )
        for idx1, lr in enumerate(listarama):
            for idx2, dato in enumerate(data):
                if dato["id"] == lr:
                    data[idx2]["opened"] = (idx1 != 0)
                    break
    elif modo == "DES":
        destino = Destino.objects.filter(pk=id).first()
        if destino:
            data = ConsultaArbol(Destino.objects.filter(
                pk__in=destino.destinoreferencias.values("documento__des_documento")
            ), can, id, excanu, expedientenro)
    return data


def ConsultaArbol(destinos, canhijos=0, padreid=None, excanu="ANX", expedienteorigen=None):
    datos = destinos.exclude(
        ultimoestado__estado=excanu
    ).annotate(
        expedientenroorigen=Value(expedienteorigen, output_field=CharField()),
        documentonro=Concat(
            F("documento__documentotipoarea__documentotipo__nombre"),
            Case(
                When(
                    Q(documento__numero__isnull=True) | Q(documento__numero=0), then=Value(" s/n ")
                ),
                default=Concat(
                    Value(" N° "),
                    Case(
                        When(
                            documento__origentipo__in=["O", "P"],
                            then=Value(settings.CONFIG_APP["DocumentoPreposDigital"])
                        ),
                        default=Value("")
                    ),
                    Cast(
                        "documento__numero",
                        output_field=CharField()
                    ),
                )
            )
        ),
        expedientenro=Case(
            When(
                documento__expediente__isnull=False,
                then=Concat(
                    F("documento__expediente__dependencia__codigo"),
                    Value("-"),
                    F("documento__expediente__anio"),
                    Value("-"),
                    LPad(
                        Cast(
                            "documento__expediente__numero",
                            output_field=CharField()
                        ),
                        settings.CONFIG_APP["ExpedienteZero"],
                        Value("0")
                    ),
                    output_field=CharField()
                )
            ),
            default=Value("")
        ),
        origennombre=F("documento__documentotipoarea__area__nombre"),
        destinonombre=Case(
            When(
                tipodestinatario="UO",
                then=Concat(
                    F("periodotrabajo__area__nombre"),
                    Case(
                        When(
                            Q(periodotrabajo__esjefe=True) | Q(periodotrabajo__tipo__in=["EN", "EP"]),
                            then=Value("")
                        ),
                        default=Concat(
                            Value(" - "),
                            F("periodotrabajo__iniciales")
                        )
                    )
                )
            ),
            When(
                tipodestinatario="PJ",
                then=Concat(
                    Case(
                        When(
                            personajuridica__nombrecomercial__isnull=True, then=F("personajuridica__razonsocial")
                        ),
                        default=F("personajuridica__nombrecomercial")
                    ),
                    Case(
                        When(
                            persona__isnull=False,
                            then=Concat(
                                Value(" - "),
                                F("persona__apellidocompleto")
                            )
                        ),
                        default=Value("")
                    )
                )
            ),
            When(
                tipodestinatario="CI",
                then=F("persona__apellidocompleto"),
            ),
            default=Value("")
        ),
        hijos=Count(
            "destinoreferencias", filter=~Q(destinoreferencias__documento__ultimoestado__estado=excanu)
        ),
        canhijos=Value(canhijos),
        opened=Case(
            When(
                Q(hijos__gt=0, canhijos__gt=0),
                then=Value(True)
            ),
            default=Value(False)
        ),
        padre=Value(padreid, output_field=IntegerField()),
        destinoestado=F("ultimoestado__estado")
    ).order_by(
        "creado",
        "documento__documentotipoarea__documentotipo__nombre",
        "documento__numero",
        "documento__origentipo",
        "documento__expediente",
        "documento__expediente__dependencia__codigo",
        "documento__expediente__anio",
        "documento__expediente__numero",
        "documento__documentotipoarea__area__nombre",
        "periodotrabajo__area__nombre",
        "periodotrabajo__esjefe",
        "periodotrabajo__tipo",
        "periodotrabajo__iniciales",
        "personajuridica__nombrecomercial",
        "personajuridica__razonsocial",
        "persona__apellidocompleto",
        "tipodestinatario",
        "persona"
    ).distinct().values(
        "id",
        "expedientenroorigen",
        "documentonro",
        "expedientenro",
        "origennombre",
        "destinonombre",
        "hijos",
        "opened",
        "padre",
        "destinoestado"
    )
    _result = list(datos)
    if canhijos > 0:
        _hijos = []
        for padre in _result:
            if padre["hijos"] > 0:
                destino = Destino.objects.get(pk=padre["id"])
                # print(expedienteorigen)
                _hijos = _hijos + ConsultaArbol(Destino.objects.filter(
                    pk__in=destino.destinoreferencias.values("documento__des_documento")
                ), canhijos - 1, padre["id"], excanu, expedienteorigen)
        _result = _result + _hijos
    return _result
