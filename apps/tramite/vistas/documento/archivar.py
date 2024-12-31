"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.formularios.documentoarchivar import DocumentoArchivarForm, DocumentoDesarchivarForm
from apps.tramite.models import Destino, DestinoEstado
from modulos.utiles.clases.crud import VistaEdicion


class DocumentoArchivar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/archivar/formulario.html"
    model = Destino
    form_class = DocumentoArchivarForm

    def get_form(self, form_class=None):
        form = super(DocumentoArchivar, self).get_form(form_class)
        form.fields["fecha"].widget.attrs["data-startdate"] = self.object.creado.strftime("%Y-%m-%d")
        form.fields["fecha"].widget.attrs["data-enddate"] = datetime.datetime.now().strftime("%Y-%m-%d")
        return form

    def get_context_data(self, **kwargs):
        context = super(DocumentoArchivar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Archivar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.ultimoestado.estado != "AR":
                DestinoEstado.objects.create(
                    destino=destino,
                    estado="AR",
                    creador=self.request.user,
                    fecha=form.cleaned_data["fecha"],
                    observacion=form.cleaned_data.get("observacion")
                )
            SocketMsg(
                tipo="info",
                clase="bg-dark",
                userid=self.request.user.pk,
                titulo="Bandeja Recepcionados",
                mensaje="Se archivó el documento correctamente",
                funcpost='refrescarTableros("dbRecepcionados", true)'
            )
            context["archivado"] = True
        return self.render_to_response(context)


class DocumentoDesarchivar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/desarchivar/formulario.html"
    model = Destino
    form_class = DocumentoDesarchivarForm

    def get_context_data(self, **kwargs):
        context = super(DocumentoDesarchivar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Desarchivar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            destino = self.get_object()
            if destino.ultimoestado.estado == "AR":
                desest = DestinoEstado.objects.create(
                    destino=destino,
                    estado="RE",
                    creador=self.request.user,
                    observacion="DESARCHIVADO"
                )
                destino.ultimoestado = desest
                destino.save()
            SocketMsg(
                tipo="info",
                clase="bg-dark",
                userid=self.request.user.pk,
                titulo="Bandeja Recepcionados",
                mensaje="Se archivó el documento correctamente",
                funcpost='refrescarTableros("dbRecepcionados", true)'
            )
            context["desarchivado"] = True
        return self.render_to_response(context)
