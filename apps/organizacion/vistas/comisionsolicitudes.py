"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.utils import timezone

from apps.organizacion.formularios.integrante import FormPresidenteAprobar
from apps.organizacion.models import PeriodoTrabajo
from apps.organizacion.tablas.comisionsolicitudes import TablaComisionSolicitudes
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaEdicion, VistaEliminacion


class ComisionSolicitudesListar(FeedDataView):
    token = TablaComisionSolicitudes.token

    def get_queryset(self):
        qs = PeriodoTrabajo.objects.filter(
            area__areatipo__paracomision=True,
            activo=False,
            aprobador__isnull=True,
            fin__isnull=True,
            cargo__esprincipal=True,
            documentosustento__isnull=False
        ).exclude(
            area__padre__isnull=True
        )
        return qs

    def sort_queryset(self, queryset):
        qs = super(ComisionSolicitudesListar, self).sort_queryset(queryset)
        if len(self.order_args) == 0:
            qs = qs.order_by("creado")
        return qs

    def get_context_data(self, **kwargs):
        context = super(ComisionSolicitudesListar, self).get_context_data(**kwargs)
        context["solicitudes"] = self.get_queryset().count()
        return context


class ComisionSolicitudesAprobar(VistaEdicion):
    template_name = "organizacion/integrante/aprobar.html"
    model = PeriodoTrabajo
    form_class = FormPresidenteAprobar
    extra_context = {
        "botonguardartexto": "Aprobar"
    }

    def form_valid(self, form):
        context = self.get_context_data()
        presidenteNuevo = self.get_object()
        if not presidenteNuevo.aprobador and presidenteNuevo.cargo.esprincipal and not presidenteNuevo.fin:
            presidenteNuevo.aprobador = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            presidenteNuevo.activo = True
            presidenteNuevo.save()
            areaActual = presidenteNuevo.area
            areaActual.jefeactual = presidenteNuevo
            areaActual.save()
        context["form"] = form
        return self.render_to_response(context)


class ComisionSolicitudesAnular(VistaEliminacion):
    template_name = "organizacion/integrante/anular.html"
    model = PeriodoTrabajo

    def get_context_data(self, **kwargs):
        context = super(ComisionSolicitudesAnular, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Anular"
        return context
