"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.models import Destino, DestinoEstado
from apps.tramite.tablas.oficinaentrada import TablaOficinaEntrada
from apps.tramite.vistas.bandejas import BandejaListarFeedDataView, BandejaVista


class OficinaBandejaEntrada(BandejaVista):
    template_name = "tramite/oficina/entrada/vista.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["TablaOficinaEntrada"] = TablaOficinaEntrada(request=request)
        return self.render_to_response(context=context)


class OficinaBandejaEntradaListar(BandejaListarFeedDataView):
    table = "tablas.oficinaentrada.TablaOficinaEntrada"
    qs = "QueryOficinaBandejaEntrada"


class OficinaBandejaEntradaRecepcionMasiva(TemplateValidaLogin, TemplateView):
    template_name = "tramite/oficina/entrada/recepcionmasiva.html"
    extra_context = {
        "botonguardartexto": "<i class='fas fa-paper-plane fa-1x'></i> Recepcionar"
    }

    def get_context_data(self, **kwargs):
        context = super(OficinaBandejaEntradaRecepcionMasiva, self).get_context_data(**kwargs)
        if self.request.GET.get("ids"):
            ids = eval(self.request.GET.get("ids").replace("_", ","))
        else:
            ids = eval(self.request.POST.get("destinos").replace("_", ","))
        context["ids"] = ids
        context["destinos"] = Destino.objects.filter(pk__in=ids)
        if self.request.GET:
            entfis = context["destinos"].filter(entregafisica__isnull=False).exclude(entregafisica="")
            if entfis.count() > 0:
                _entfis = ""
                for destino in entfis:
                    _entfis += "%s_" % destino.id
                context["entfis"] = _entfis
                context["forma"] = "Firmando Cargos de Entrega Física Masiva"
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        destinos = eval(request.POST.get("destinos"))
        recok = False
        for desid in destinos:
            destino = Destino.objects.filter(pk=desid).first()
            if destino:
                recok = True
                # Recepcionamos el documento
                ultimoestado = DestinoEstado(
                    destino=destino,
                    estado="RE",
                    creador=self.request.user
                )
                ultimoestado.save()
        if recok:
            SocketMsg(
                tipo="info",
                clase="bg-dark",
                userid=self.request.user.pk,
                titulo="Bandeja Recepcionados",
                mensaje="Los documentos se recibieron correctamente",
                funcpost='refrescarTableros("dbEntrada,dbRecepcionados", true)'
            )
        context["recibirok"] = True
        return self.render_to_response(context=context)
