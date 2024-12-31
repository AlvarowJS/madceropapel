"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import PeriodoTrabajo
from apps.tramite.formularios.misencargaturas import FormEncargatura
from apps.tramite.tablas.misencargaturas import TablaEncargaturaDocumentos
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView
from modulos.datatable.views import FeedDataView


class MisEncargaturas(TemplateValidaLogin, TemplateView):
    template_name = "tramite/misencargaturas/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Mis Encargaturas"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["formEncargatura"] = FormEncargatura(request)
        context["tablaEncargaturaDocumentos"] = TablaEncargaturaDocumentos(request)
        return self.render_to_response(context=context)


class MisEncargaturasListar(BandejaListarFeedDataView):
    token = TablaEncargaturaDocumentos.token

    def get_queryset(self):
        self.filter_date = TablaEncargaturaDocumentos.opts.filter_date
        self.filter_tipodoc = TablaEncargaturaDocumentos.opts.filter_tipodoc
        qs = super(MisEncargaturasListar, self).get_queryset()
        periodotrabajo = PeriodoTrabajo.objects.filter(
            id=self.kwargs.get("pt"),
            persona=self.request.user.persona
        ).first()
        qs = qs.filter(
            origentipo="O",
            estadoemitido__isnull=False,
            responsable=periodotrabajo
        )
        return qs
