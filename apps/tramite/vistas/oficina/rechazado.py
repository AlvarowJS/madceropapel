"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.formularios.destinorechazado import RechazadoReenviarForm, RechazadoArchivarForm, RechazadoAnularForm
from apps.tramite.models import Destino, DestinoEstado
from apps.tramite.tablas.oficinarechazados import TablaOficinaRechazados
from apps.tramite.vistas.bandejas import BandejaVista, BandejaListarFeedDataView
from modulos.utiles.clases.crud import VistaEdicion


class OficinaBandejaRechazado(BandejaVista):
    template_name = "tramite/oficina/rechazado/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["TablaOficinaRechazados"] = TablaOficinaRechazados(request=request)
        return self.render_to_response(context=context)


class OficinaBandejaRechazadoListar(BandejaListarFeedDataView):
    table = "tablas.oficinarechazados.TablaOficinaRechazados"
    qs = "QueryOficinaBandejaRechazados"


class OficinaBandejaRechazadoReenviar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/oficina/rechazado/reenviar.html"
    model = Destino
    form_class = RechazadoReenviarForm
    extra_context = {
        "botonguardartexto": "Reenviar"
    }

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.ultimoestado.estado == "RH":
                destinoestado = DestinoEstado.objects.create(
                    destino=destino,
                    estado="NL",
                    creador=self.request.user,
                    observacion=form.cleaned_data.get("observacion")
                )
                destino.ultimoestado = destinoestado
                destino.save()
            # Notificamos al Destino
            SocketMsg(userid=self.request.user.id, funcpost='refrescarTableros("dbRechazados", true)')
            SocketMsg(
                tipo='primary',
                clase='bg-danger',
                userid=destino.periodotrabajo.persona.usuario.pk,
                titulo='Bandeja de Entrada',
                mensaje='%s, %s' % (
                    "Hola %s" % destino.periodotrabajo.persona.nombres,
                    "le han <strong>REENVIADO</strong> un documento que Ud. había rechazado."
                ),
                funcpost='refrescarTableros("dbEntrada", true)'
            )
            context["reenviook"] = True
        return self.render_to_response(context)


class OficinaBandejaRechazadoAnular(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/oficina/rechazado/anular.html"
    model = Destino
    form_class = RechazadoAnularForm
    extra_context = {
        "botonguardartexto": "Anular"
    }

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
        #     if destino.ultimoestado.estado == "RH":
        #         destinoestado = DestinoEstado.objects.create(
        #             destino=destino,
        #             estado="AR",
        #             creador=self.request.user,
        #             observacion=form.cleaned_data.get("observacion")
        #         )
        #         destino.ultimoestado = destinoestado
        #     SocketMsg(userid=self.request.user.id, funcpost='refrescarTableros("dbRechazados", true)')
            context["anuladook"] = True
        return self.render_to_response(context)


class OficinaBandejaRechazadoArchivar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/oficina/rechazado/archivar.html"
    model = Destino
    form_class = RechazadoArchivarForm
    extra_context = {
        "botonguardartexto": "Archivar"
    }

    def get_form(self, form_class=None):
        form = super(OficinaBandejaRechazadoArchivar, self).get_form(form_class)
        form.fields["fecha"].widget.attrs["data-startdate"] = self.object.creado.strftime("%Y-%m-%d")
        form.fields["fecha"].widget.attrs["data-enddate"] = datetime.datetime.now().strftime("%Y-%m-%d")
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.ultimoestado.estado == "RH":
                destinoestado = DestinoEstado.objects.create(
                    destino=destino,
                    estado="AR",
                    creador=self.request.user,
                    observacion=form.cleaned_data.get("observacion")
                )
                destino.ultimoestado = destinoestado
            SocketMsg(userid=self.request.user.id, funcpost='refrescarTableros("dbRechazados", true)')
            context["archivadook"] = True
        return self.render_to_response(context)
