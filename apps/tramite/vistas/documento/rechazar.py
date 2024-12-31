"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.formularios.documentorechazar import DocumentoRechazarForm
from apps.tramite.models import Destino, DestinoEstado
from modulos.utiles.clases.crud import VistaEdicion


class DocumentoRechazar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/rechazar/formulario.html"
    model = Destino
    form_class = DocumentoRechazarForm

    def get_context_data(self, **kwargs):
        context = super(DocumentoRechazar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Rechazar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.ultimoestado.estado != "RH":
                DestinoEstado.objects.create(
                    destino=destino,
                    estado="RH",
                    creador=self.request.user,
                    observacion=form.cleaned_data.get("observacion")
                )
            SocketMsg(
                tipo="info",
                clase="bg-dark",
                userid=self.request.user.pk,
                titulo="Bandeja Recepcionados",
                mensaje="Se RECHAZÓ el documento correctamente",
                funcpost='refrescarTableros("dbEntrada", true)'
            )
            # Notificamos al emisor
            if destino.documento.responsable:
                SocketMsg(
                    userid=destino.documento.responsable.persona.usuario.pk,
                    funcpost='refrescarTableros("dbEmitidos,dbRechazados", true)'
                )
                if destino.documento.responsable.persona.usuario != destino.documento.creador:
                    SocketMsg(
                        userid=destino.documento.creador.pk,
                        funcpost='refrescarTableros("dbEmitidos,dbRechazados", true)'
                    )
            context["rechazado"] = True
        return self.render_to_response(context)
