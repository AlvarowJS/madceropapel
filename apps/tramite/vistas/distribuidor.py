"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from datetime import datetime

from django.db.models import ProtectedError
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.formularios.distribuidor import FormDistribuidor
from apps.tramite.models import Distribuidor
from apps.tramite.tablas.distribuidor import TablaDistribuidores
from apps.tramite.vistas.varios import ConsultarRUC, ConsultarDNI
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEliminacion, VistaEdicion
from modulos.utiles.clases.ruc import ClaseRUC


class DistribuidorInicio(TemplateValidaLogin, TemplateView):
    template_name = "tramite/distribuidor/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Distribuidores de Mensajería"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["TablaDistribuidor"] = TablaDistribuidores(request)
        return self.render_to_response(context=context)


class DistribuidorListar(FeedDataView):
    token = TablaDistribuidores.token

    def get_queryset(self):
        qs = super(DistribuidorListar, self).get_queryset()
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
        qs = qs.filter(
            arearindente=arearindente
        )
        return qs


class DistribuidorAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/distribuidor/formulario.html"
    model = Distribuidor
    form_class = FormDistribuidor
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def get_form(self, form_class=None):
        form = super(DistribuidorAgregar, self).get_form(form_class)
        del form.fields["estado"]
        form.fields["inicio"].initial = datetime.now().date()
        return form

    def form_valid(self, form):
        if form.is_valid():
            periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
            form.instance.arearindente = arearindente
            return super(DistribuidorAgregar, self).form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        fi = super(DistribuidorAgregar, self).form_invalid(form)
        print(form.errors)
        return fi


class DistribuidorEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/distribuidor/formulario.html"
    model = Distribuidor
    form_class = FormDistribuidor
    permitir_desde = [
        reverse_lazy("appini:inicio")
    ]

    def get_form(self, form_class=None):
        form = super(DistribuidorEditar, self).get_form(form_class)
        if self.get_object().tipo == "M":
            form.fields["personadni"].initial = self.get_object().persona.numero
        elif self.get_object().tipo == "C":
            form.fields["personajuridicaruc"].initial = self.get_object().personajuridica.ruc
        return form

    def form_valid(self, form):
        if form.is_valid():
            return super(DistribuidorEditar, self).form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        fi = super(DistribuidorEditar, self).form_invalid(form)
        print(form.errors)
        return fi


class DistribuidorEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "tramite/distribuidor/eliminar.html"
    model = Distribuidor


class DistribuidorConsultaRuc(TemplateValidaLogin, TemplateView):
    template_name = "tramite/distribuidor/consultaruc.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        ruc = request.POST.get("ruc")
        cr = ClaseRUC('')
        pj = None
        if cr.ValidarRUC(ruc):
            pj, estado = ConsultarRUC(ruc, request)
            if estado:
                context["errorconsulta"] = estado
        else:
            context["ruc_no_valido"] = True
        fd = FormDistribuidor(data={
            "personajuridica": pj
        })
        context["form"] = fd
        return self.render_to_response(context=context)


class DistribuidorConsultaDni(TemplateValidaLogin, TemplateView):
    template_name = "tramite/distribuidor/consultadni.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        dni = request.POST.get("dni")
        td = request.POST.get("td")
        per, estado = ConsultarDNI(dni, request)
        fd = FormDistribuidor(data={
            "persona": per,
        })
        if estado:
            context["errorconsulta"] = estado
        context["form"] = fd
        return self.render_to_response(context=context)
