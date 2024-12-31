"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Q, Value, Count
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import PeriodoTrabajo, TrabajadoresActuales
from apps.tramite.models import Documento
from apps.tramite.tablas.mesapartesregistrados import TablaMesaPartesRegistrados
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView, QueryMesaPartesBandejaRegistrados
from apps.tramite.vistas.documento.registrarmesapartes import EmitirMesaDePartes


class MesaPartesBandejaRegistrados(BandejaVista):
    template_name = "tramite/mesapartes/registrados/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
        if not periodoactual.area.esrindente:
            context["MesaPartesTrabajadores"] = TrabajadoresActuales().filter(
                area__esrindente=False,
                area__rindentepadre__isnull=True,
                permisotramite="T"
            ).order_by("persona__nombres", "persona__paterno", "persona__materno")
        else:
            context["MesaPartesTrabajadores"] = TrabajadoresActuales().filter(
                # area__mesadepartes=True,
                permisotramite="T"
            ).filter(
                Q(area__esrindente=True)
                |
                Q(area__rindentepadre__isnull=False)
            ).filter(
                Q(area=periodoactual.area)
                |
                Q(
                    area__rindentepadre__isnull=False,
                    area__rindentepadre=periodoactual.area
                )
                |
                Q(
                    area__rindentepadre__isnull=False,
                    area__rindentepadre=periodoactual.area.rindentepadre
                )
            ).order_by("persona__nombres", "persona__paterno", "persona__materno")
        context["TablaMesaPartesRegistrados"] = TablaMesaPartesRegistrados(request=request)
        return self.render_to_response(context=context)


class MesaPartesBandejaRegistradosListar(BandejaListarFeedDataView):
    table = "tablas.mesapartesregistrados.TablaMesaPartesRegistrados"
    qs = "QueryMesaPartesBandejaRegistrados"

    def get_queryset(self):
        qs = super(MesaPartesBandejaRegistradosListar, self).get_queryset()
        #
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        qs = qs.annotate(
            periodoactualid=Value(periodoactual.pk)
        )
        if not periodoactual.area.esrindente:
            qs = qs.filter(
                emisor__area__esrindente=False,
                emisor__area__rindentepadre__isnull=True
            )
        else:
            qs = qs.filter(
                Q(emisor__area__esrindente=True)
                |
                Q(emisor__area__rindentepadre__isnull=False)
            ).filter(
                Q(emisor__area=periodoactual.area)
                |
                Q(
                    emisor__area__rindentepadre__isnull=False,
                    emisor__area__rindentepadre=periodoactual.area
                )
                |
                Q(
                    emisor__area__rindentepadre__isnull=False,
                    emisor__area__rindentepadre=periodoactual.area.rindentepadre
                )
            )
        #
        users = self.kwargs.get("users")
        if users != "_":
            users = list(map(int, users.split("_")[1:]))
            qs = qs.filter(
                creador__in=users
            )
        modo = self.kwargs.get("modo")
        if modo not in ["P", "E", "R"]:
            qs = qs.filter(pk=-100)
        #
        self.emitidos = qs.filter(
            ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"]
        ).count()
        self.pendientes = qs.exclude(
            ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"]
        ).count()
        self.rechazados = qs.filter(
            des_documento__ultimoestado__estado="RH"
        ).count()
        #
        if modo == "P":
            qs = qs.exclude(ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"])
        elif modo == "E":
            qs = qs.filter(ultimoestado__estado__in=["EM", "RP", "RT", "AT", "AR"])
        elif modo == "R":
            qs = qs.filter(des_documento__ultimoestado__estado="RH")
        return qs

    def sort_queryset(self, queryset):
        qs = super(BandejaListarFeedDataView, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("-expediente__anio", "-expediente__numero")
        return qs

    def get_context_data(self, **kwargs):
        context = super(BandejaListarFeedDataView, self).get_context_data(**kwargs)
        context['modos'] = {
            "data": [
                {"id": "P", "nombre": "Pendientes", "cantidad": self.pendientes, "color": "warning"},
                {"id": "E", "nombre": "Emitidos", "cantidad": self.emitidos, "color": "primary"},
                {"id": "R", "nombre": "Rechazados", "cantidad": self.rechazados, "color": "danger"}
            ]
        }
        return context


class MesaPartesBandejaRegistradosEmisionMasiva(TemplateValidaLogin, TemplateView):
    template_name = "tramite/mesapartes/registrados/emisionmasiva.html"
    extra_context = {
        "botonguardartexto": "<i class='fas fa-paper-plane fa-1x'></i> Emitir"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        documentos = eval(request.POST.get("documentos"))
        for docid in documentos:
            doc = Documento.objects.filter(pk=docid).first()
            EmitirMesaDePartes(doc, request)
        context["emisionok"] = True
        return self.render_to_response(context=context)
