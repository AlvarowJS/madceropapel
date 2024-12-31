"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import FormView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.formularios.mimensajeria import FormMesaPartesMiMensajeria, MiMensajeriaAccionesForm
from apps.tramite.models import Destino, DestinoEstadoMensajeria, CargoExternoDetalle
from apps.tramite.tablas.mesapartesmimensajeria import TablaMesaPartesMiMensajeria
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView
from modulos.utiles.clases.crud import VistaEdicion


class MesaPartesMiMensajeria(BandejaVista):
    template_name = "tramite/mesapartes/mimensajeria/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["FormMesaPartesMiMensajeria"] = FormMesaPartesMiMensajeria()
        context["TablaMesaPartesMiMensajeria"] = TablaMesaPartesMiMensajeria(request=request)
        return self.render_to_response(context=context)


class MesaPartesMiMensajeriaListar(BandejaListarFeedDataView):
    table = "tablas.mesapartesmimensajeria.TablaMesaPartesMiMensajeria"
    qs = "QueryOficinaBandejaMiMensajeria"

    def get_queryset(self):
        query = super(MesaPartesMiMensajeriaListar, self).get_queryset()
        modo = self.request.GET.get("modo")
        if modo == "D":
            query = query.filter(
                ultimoestadomensajeria__estado__in=["DM", "DA"]
            )
        elif modo == "N":
            query = query.exclude(
                ultimoestadomensajeria__estado__in=["DM", "DA"]
            )
        return query


class MesaPartesMiMensajeriaAcciones(VistaEdicion):
    template_name = "tramite/mesapartes/mimensajeria/acciones.html"
    model = Destino
    form_class = MiMensajeriaAccionesForm
    reenviar = False

    def get_form(self, form_class=None):
        form = super(MesaPartesMiMensajeriaAcciones, self).get_form(form_class)
        if self.get_object().ultimoestadomensajeria.estado in ["FD", "EC", "ED"]:
            self.reenviar = True
            del form.fields["amodo"]
            del form.fields["atodos"]
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesMiMensajeriaAcciones, self).get_context_data(**kwargs)
        if self.reenviar:
            context["botonguardartexto"] = "Enviar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if form.cleaned_data.get("atodos"):
                for destino in destino.documento.des_documento.filter(ultimoestadomensajeria__estado__in=["DM", "DA"]):
                    DestinoEstadoMensajeria.objects.create(
                        destino=destino,
                        estado=form.cleaned_data["amodo"],
                        observacion=form.cleaned_data.get("aobservacion"),
                        creador=self.request.user
                    )
            else:
                DestinoEstadoMensajeria.objects.create(
                    destino=destino,
                    estado=form.cleaned_data.get("amodo", "PE"),
                    observacion=form.cleaned_data.get("aobservacion"),
                    creador=self.request.user
                )
            SocketMsg(
                userid=self.request.user.pk,
                funcpost='refrescarTableros("dbMiMensajeria", true)'
            )
            context["mensajeriaok"] = True
        return self.render_to_response(context)


class MesaPartesMiMensajeriaAccionesFull(TemplateValidaLogin, FormView):
    template_name = "tramite/mesapartes/mimensajeria/accionesfull.html"
    form_class = MiMensajeriaAccionesForm

    def get_form(self, form_class=None):
        form = super(MesaPartesMiMensajeriaAccionesFull, self).get_form(form_class)
        del form.fields["atodos"]
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesMiMensajeriaAccionesFull, self).get_context_data(**kwargs)
        context["ids"] = self.request.GET.get("ids")
        self.ids = str(context["ids"])[:-1].split("_")
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            for destino in Destino.objects.filter(pk__in=self.ids):
                DestinoEstadoMensajeria.objects.create(
                    destino=destino,
                    estado=form.cleaned_data["amodo"],
                    observacion=form.cleaned_data.get("aobservacion"),
                    creador=self.request.user
                )
            SocketMsg(
                userid=self.request.user.pk,
                funcpost='refrescarTableros("dbMiMensajeria", true)'
            )
            context["mensajeriaok"] = True
        return self.render_to_response(context)
