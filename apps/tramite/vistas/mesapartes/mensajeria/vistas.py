"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import datetime

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import FormView, DetailView, TemplateView
from rest_framework import views, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.formularios.mensajeria import DestinoMensajeriaFinalizarDirectoForm
from apps.tramite.formularios.mesapartesenviar import FormDestinoPlanilladoAgregar, FormDestinoPlanilladoEnviar, \
    FormDestinoPlanilladoFinalizar, FormDestinoPlanilladoCargo, FormDestinoPlanilladoRectificar
from apps.tramite.formularios.mesapartesrecibir import DestinoMensajeriaRecibir, DestinoMensajeriaDevolver
from apps.tramite.models import Destino, DestinoEstadoMensajeria, CargoExterno, CargoExternoDetalle, \
    AmbitoMensajeria, CargoExternoEstado
from apps.tramite.vistas.plantillas.cargoexterno import MensajeriaPlanilladoVista
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion


class MesaPartesMensajeriaRecibir(TemplateValidaLogin, FormView):
    template_name = "tramite/mesapartes/mensajeria/recibir.html"
    form_class = DestinoMensajeriaRecibir

    def get_context_data(self, **kwargs):
        context = super(MesaPartesMensajeriaRecibir, self).get_context_data(**kwargs)
        self.ids = str(self.kwargs.get("ids"))[:-1].split("_")
        context["destinos"] = Destino.objects.filter(pk__in=self.ids).order_by(
            "documento__expediente__numero",
            "ultimoestadomensajeria__creado"
        )
        context["botonguardartexto"] = "<i class='fas fa-check fa-1x'></i> Recibir"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            for destino in Destino.objects.filter(pk__in=self.ids):
                DestinoEstadoMensajeria.objects.create(
                    destino=destino,
                    estado="RM",
                    creador=self.request.user
                )
            context["recepcionok"] = True
        return self.render_to_response(context)


class MesaPartesPlanilladoAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/mesapartes/mensajeria/enviar.html"
    form_class = FormDestinoPlanilladoAgregar
    model = CargoExterno

    def get_context_data(self, **kwargs):
        context = super(MesaPartesPlanilladoAgregar, self).get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo")
        modo = self.kwargs.get("modo")
        if modo == "T":
            modo = "N"
        if modo in ["T", "N", "R", "L"]:
            self.ids = str(self.kwargs.get("ids"))[:-1].split("_")
            context["destinos"] = Destino.objects.filter(pk__in=self.ids).order_by(
                "documento__expediente__numero",
                "ultimoestadomensajeria__creado"
            )
            if tipo == "NP":
                context["botonguardartexto"] = "<i class='fas fa-save fa-1x'></i> Generar"
            else:
                context["botonguardartexto"] = "<i class='fas fa-plus fa-1x'></i> Agregar"
            context["mododistribucion"] = AmbitoMensajeria.objects.get(codigo=modo)
        else:
            if tipo == "NP":
                context["noambito"] = "crear"
            else:
                context["noambito"] = "agregar documentos a"
            context["noBotonGuardar"] = True
            context["botoncancelartexto"] = "Cerrar"
        return context

    def get_form(self, form_class=None):
        form = super(MesaPartesPlanilladoAgregar, self).get_form(form_class)
        tipo = self.kwargs.get("tipo")
        del form.fields["destinos"]
        modo = self.kwargs.get("modo")
        if modo == "T":
            modo = "N"
        form.fields["ambito"].initial = AmbitoMensajeria.objects.get(codigo=modo)
        if tipo == "NP":
            form.fields["fecha"].initial = datetime.datetime.now().date
            form.fields["distribuidortipo"].initial = "M" if modo == "L" else "C"
            periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
            arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
            form.fields["distribuidor"].queryset = form.fields["distribuidor"].queryset.filter(
                arearindente=arearindente
            )
            del form.fields["anio"]
            del form.fields["planillado"]
        else:
            periodoactual = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            arearindente = periodoactual.area.esrindente or periodoactual.area.rindentepadre
            form.fields["planillado"].queryset = form.fields["planillado"].queryset.filter(
                ultimoestado__estado="GN",
                # ambito__codigo=modo
            )
            if arearindente:
                form.fields["planillado"].queryset = form.fields["planillado"].queryset.filter(
                    emisorarearindente=arearindente
                )
            else:
                form.fields["planillado"].queryset = form.fields["planillado"].queryset.filter(
                    emisorarearindente__isnull=True
                )
            del form.fields["ambito"]
            del form.fields["distribuidortipo"]
            del form.fields["distribuidor"]
            del form.fields["fecha"]
            del form.fields["nota"]
        return form

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            tipo = self.kwargs.get("tipo")
            # modo = self.kwargs.get("modo")
            # if modo == "T":
            #     modo = "N"
            destinos = Destino.objects.filter(pk__in=self.ids)
            destinosyaplanillado = []
            # Validamos si los destinos no están en estado de mensajería GN
            for destino in destinos:
                if not destino.ultimoestadomensajeria.estado in ["RA", "RM"]:
                    destinosyaplanillado.append(destino.pk)
                    form.add_error(None, "El documento %s, está en un Planillado N° %s" % (
                        destino.documentonro,
                        destino.detallemensajeria.cargoexterno.Numero()
                    ))
            if not form.non_field_errors():
                periodoactual = self.request.user.persona.periodotrabajoactual(
                    self.request.session.get("cambioperiodo")
                )
                if tipo == "NP":
                    # form.instance.ambito = AmbitoMensajeria.objects.get(codigo=modo)
                    form.instance.emisortrabajador = periodoactual
                    form.instance.creador = self.request.user
                    form.save()
                    CargoExternoEstado.objects.create(
                        cargoexterno=form.instance,
                        estado="GN",
                        creador=self.request.user
                    )
                    for destino in destinos:
                        DestinoEstadoMensajeria.objects.create(
                            destino=destino,
                            estado="GN",
                            creador=self.request.user
                        )
                        ced = CargoExternoDetalle.objects.create(
                            cargoexterno=form.instance,
                            destino=destino,
                            creador=self.request.user
                        )
                        destino.detallemensajeria = ced
                        destino.save()
                    context["generadook"] = form.instance.pk
                    context["generadonumero"] = form.instance.NumeroFull()
                else:
                    cargoexterno = form.cleaned_data["planillado"]
                    for destino in destinos:
                        DestinoEstadoMensajeria.objects.create(
                            destino=destino,
                            estado="GN",
                            creador=self.request.user
                        )
                        ced = CargoExternoDetalle.objects.create(
                            cargoexterno=cargoexterno,
                            destino=destino,
                            creador=self.request.user
                        )
                        destino.detallemensajeria = ced
                        destino.save()
                    context["agregadook"] = cargoexterno.pk
                    context["agregadonumero"] = cargoexterno.NumeroFull()
            else:
                context["destinosyaplanillado"] = destinosyaplanillado
            context["form"] = form
        return self.render_to_response(context)


class MesaPartesPlanilladoEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/mensajeria/enviar.html"
    form_class = FormDestinoPlanilladoAgregar
    model = CargoExterno

    def get_form(self, form_class=None):
        form = super(MesaPartesPlanilladoEditar, self).get_form(form_class)
        del form.fields["anio"]
        del form.fields["planillado"]
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        arearindente = periodoactual.area if periodoactual.area.esrindente else periodoactual.area.rindentepadre
        form.fields["distribuidor"].queryset = form.fields["distribuidor"].queryset.filter(
            arearindente=arearindente
        )
        form.fields["distribuidortipo"].initial = form.instance.distribuidor.tipo
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesPlanilladoEditar, self).get_context_data(**kwargs)
        destinos = list(self.get_object().destinos.values_list("destino_id", flat=True))
        context["destinos"] = Destino.objects.filter(
            pk__in=destinos
        ).order_by(
            "documento__expediente__numero",
            "ultimoestadomensajeria__creado"
        )
        context["form"].fields["destinos"].initial = destinos
        context["botonguardartexto"] = "<i class='fas fa-save fa-1x'></i> Guardar"
        context["botoncancelartexto"] = "Cerrar"
        context["mododistribucion"] = self.get_object().ambito
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            form.save()
            destinos = eval(form.cleaned_data["destinos"])
            destinosquitados = Destino.objects.filter(
                pk__in=self.get_object().destinos.values_list("destino_id")
            ).exclude(
                pk__in=destinos
            )
            for destino in destinosquitados:
                estadoanterior = destino.estadosmensajeria.order_by("-creado").filter(
                    pk__lt=destino.ultimoestadomensajeria.pk
                ).first()
                detmsg = destino.detallemensajeria
                destino.ultimoestadomensajeria = estadoanterior
                destino.detallemensajeria = None
                destino.save()
                detmsg.delete()
            context["editadook"] = form.instance.pk
            context["editadonro"] = form.instance.NumeroFull()
        return self.render_to_response(context)


class MesaPartesPlanilladoEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "tramite/mesapartes/mensajeria/eliminar.html"
    model = CargoExterno

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        try:
            cargoexterno = self.object
            destinos = Destino.objects.filter(
                pk__in=cargoexterno.destinos.values_list("destino_id")
            )
            for destino in destinos:
                estadoanterior = destino.estadosmensajeria.order_by("-creado").filter(
                    pk__lt=destino.ultimoestadomensajeria.pk
                ).first()
                detmsg = destino.detallemensajeria
                destino.ultimoestadomensajeria = estadoanterior
                destino.detallemensajeria = None
                destino.save()
                detmsg.delete()
            cargoexterno.ultimoestado = None
            cargoexterno.save()
            cargoexterno.estados.all().delete()
            self.object.delete()
            context["anulacionok"] = True
        except Exception as e:
            context["errordelete"] = "El registro no pudo ser eliminado"
        _result = self.render_to_response(context)
        return _result


class MesaPartesPlanilladoRectificar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/mensajeria/rectificar.html"
    form_class = FormDestinoPlanilladoRectificar
    model = CargoExternoDetalle

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            form.save()
        return self.render_to_response(context)


class MesaPartesPlanilladoCerrar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/mensajeria/cerrar.html"
    form_class = FormDestinoPlanilladoEnviar
    model = CargoExterno

    def get_context_data(self, **kwargs):
        context = super(MesaPartesPlanilladoCerrar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "<i class='fas fa-lock fa-1x'></i> Cerrar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            CargoExternoEstado.objects.create(
                cargoexterno=self.get_object(),
                estado="CE",
                creador=self.request.user
            )
            context["enviadook"] = form.instance.pk
            context["enviadonro"] = form.instance.Numero()
        return self.render_to_response(context)


class MesaPartesPlanilladoReAbrir(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/mensajeria/reabrir.html"
    form_class = FormDestinoPlanilladoEnviar
    model = CargoExterno

    def get_context_data(self, **kwargs):
        context = super(MesaPartesPlanilladoReAbrir, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "<i class='fas fa-lock-open fa-1x'></i> Re-Abrir"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            cargoexterno = self.get_object()
            cargoexterno.cargopdf = None
            cargoexterno.cargofecha = None
            cargoexterno.cargoobservacion = None
            cargoexterno.save()
            CargoExternoEstado.objects.create(
                cargoexterno=cargoexterno,
                estado="GN",
                creador=self.request.user
            )
            context["noenviadook"] = form.instance.pk
            context["noenviadonro"] = form.instance.Numero()
        return self.render_to_response(context)


class MesaPartesPlanilladoExportar(views.APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        como = str(request.GET.get("como", "x")).lower()
        modo = request.GET.get("modo", "0")
        cargoexterno = CargoExterno.objects.filter(pk=pk).first()
        formatos = [
            {"como": "pdf", "ext": "pdf", "type": "application/pdf"},
            {"como": "xls", "ext": "xlsx", "type": "application/vnd.ms-excel"}
            # {"como": "xls", "ext": "xlsx", "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        ]
        regformat = next((formato for formato in formatos if formato["como"] == como), None)
        if cargoexterno and regformat:
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type=regformat["type"]
            )
            nombre = "Planillado%s.%s" % (cargoexterno.NumeroFull(), regformat["ext"])
            modo = "inline" if modo == "1" else "attachment"
            response["Content-Disposition"] = "%s; filename=%s" % (modo, nombre)
            # Creamos la plantilla y la enviamos al cliente
            pshtml = MensajeriaPlanilladoVista(*args, **kwargs)
            pshtml.kwargs = self.kwargs
            pshtml.request = self.request
            context = self.get_renderer_context()
            context["configapp"] = settings.CONFIG_APP
            response.write(pshtml.render_to_response(context=context).getvalue())
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class MesaPartesPlanilladoFinalizar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/mensajeria/finalizar.html"
    form_class = FormDestinoPlanilladoFinalizar
    model = CargoExterno

    def get_context_data(self, **kwargs):
        context = super(MesaPartesPlanilladoFinalizar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "<i class='fas fa-check fa-1x'></i> Finalizar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            cargoexterno = self.get_object()
            for ced in cargoexterno.destinos.filter(estado="RE"):
                DestinoEstadoMensajeria.objects.create(
                    ced.destino,
                    estado="NE",
                    fecha=timezone.now().date(),
                    observacion=ced.cargocomentario,
                    creador=self.request.user
                )
            for ced in cargoexterno.destinos.filter(estado="ET"):
                DestinoEstadoMensajeria.objects.create(
                    destino=ced.destino,
                    estado="FI",
                    fecha=timezone.now().date(),
                    observacion="ENTREGADO",
                    creador=self.request.user
                )
            CargoExternoEstado.objects.create(
                cargoexterno=cargoexterno,
                estado="FI",
                creador=self.request.user
            )
            context["finalizadook"] = form.instance.pk
            context["finalizadonro"] = form.instance.Numero()
        return self.render_to_response(context)


class MesaPartesPlanilladoCargo(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/mensajeria/cargo.html"
    form_class = FormDestinoPlanilladoCargo
    model = CargoExterno

    def get_form(self, form_class=None):
        form = super(MesaPartesPlanilladoCargo, self).get_form(form_class)
        cargoexterno = self.get_object()
        if cargoexterno.cargopdf:
            form.fields["cargoarchivo"].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesPlanilladoCargo, self).get_context_data(**kwargs)
        destinos = list(self.get_object().destinos.values_list("destino_id", flat=True))
        context["destinos"] = Destino.objects.filter(
            pk__in=destinos
        ).order_by(
            "documento__expediente__numero",
            "ultimoestadomensajeria__creado"
        )
        context["form"].fields["destinos"].initial = destinos
        context["botonguardartexto"] = "<i class='fas fa-check fa-1x'></i> Cargar"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            if form.cleaned_data.get("cargoarchivo"):
                form.instance.cargopdf = form.cleaned_data["cargoarchivo"].read()
            form.save()
            # Debemos subir el archivo y observar si a algunos de los documentos
            # no se pudo realizar la entrega
            destinos = list(self.get_object().destinos.values_list("destino_id", flat=True))
            datap = self.request.POST
            for numdes in destinos:
                destino = Destino.objects.get(pk=numdes)
                detallecargo = destino.detallemensajeria
                if datap.get("chkdes" + str(numdes)):
                    detallecargo.estado = "ET"
                    detallecargo.cargocomentario = None
                else:
                    # destino.detallemensajeria = None
                    # destino.save()
                    detallecargo.cargocomentario = datap.get("chkdes" + str(numdes) + "nota")
                    detallecargo.estado = "RE"
                detallecargo.save()
            context["cargook"] = form.instance.pk
            context["cargonro"] = form.instance.Numero()
        return self.render_to_response(context)


class MesaPartesPlanilladoCargoBajar(views.APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        modo = self.request.GET.get("modo", "0")
        cargoexterno = CargoExterno.objects.filter(pk=pk).first()
        if cargoexterno:
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type="application/pdf"
            )
            nombre = "Planillado%s-Cargo.pdf" % cargoexterno.NumeroFull()
            modo = "inline" if modo == "1" else "attachment"
            response["Content-Disposition"] = "%s; filename=%s" % (modo, nombre)
            response.write(cargoexterno.cargopdf)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class MesaPartesPlanilladoDetalle(TemplateValidaLogin, TemplateView):
    template_name = "tramite/mesapartes/mensajeria/detalle.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["oCE"] = CargoExterno.objects.filter(pk=self.kwargs.get("pk")).first()
        return self.render_to_response(context=context)


class MesaPartesMensajeriaDevolver(TemplateValidaLogin, FormView):
    template_name = "tramite/mesapartes/mensajeria/devolver.html"
    form_class = DestinoMensajeriaDevolver

    def get_context_data(self, **kwargs):
        context = super(MesaPartesMensajeriaDevolver, self).get_context_data(**kwargs)
        self.ids = str(self.kwargs.get("ids"))[:-1].split("_")
        context["destinos"] = Destino.objects.filter(pk__in=self.ids).order_by(
            "documento__expediente__numero",
            "ultimoestadomensajeria__creado"
        )
        context["botonguardartexto"] = "<i class='fas fa-check fa-1x'></i> Devolver"
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            documentos = []
            for destino in Destino.objects.filter(pk__in=self.ids):
                if form.cleaned_data.get("allexpediente"):
                    if not destino.documento.pk in documentos:
                        documentos.append(destino.documento.pk)
                        for destdoc in destino.documento.des_documento.exclude(ultimoestado__estado="AN"):
                            DestinoEstadoMensajeria.objects.create(
                                destino=destdoc,
                                estado="DM",
                                observacion=form.cleaned_data["observacion"],
                                creador=self.request.user
                            )
                        # Notificamos al emisor actualizando su contador de MiMensajería
                        SocketMsg(
                            userid=destino.documento.emisor.persona.usuario.pk,
                            funcpost='refrescarTableros("dbMiMensajeria", true)'
                        )
                        if destino.documento.emisor != destino.documento.responsable:
                            SocketMsg(
                                userid=destino.documento.responsable.persona.usuario.pk,
                                funcpost='refrescarTableros("dbMiMensajeria", true)'
                            )
                else:
                    DestinoEstadoMensajeria.objects.create(
                        destino=destino,
                        estado="DM",
                        observacion=form.cleaned_data["observacion"],
                        creador=self.request.user
                    )
                    # Notificamos al emisor actualizando su contador de MiMensajería
                    SocketMsg(
                        userid=destino.documento.emisor.persona.usuario.pk,
                        funcpost='refrescarTableros("dbMiMensajeria", true)'
                    )
                    if destino.documento.emisor != destino.documento.responsable:
                        SocketMsg(
                            userid=destino.documento.responsable.persona.usuario.pk,
                            funcpost='refrescarTableros("dbMiMensajeria", true)'
                        )
            context["devolucionok"] = True
        return self.render_to_response(context)


class MesaPartesMensajeriaFinalizarDirecto(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/mesapartes/mensajeria/finalizardirecto.html"
    form_class = DestinoMensajeriaFinalizarDirectoForm

    def get_form(self, form_class=None):
        form = super(MesaPartesMensajeriaFinalizarDirecto, self).get_form(form_class)
        form.fields["fecha"].widget.attrs["data-startdate"] = Destino.objects.get(
            pk=self.kwargs.get("desid")
        ).ultimoestadomensajeria.creado.strftime("%Y-%m-%d")
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesMensajeriaFinalizarDirecto, self).get_context_data(**kwargs)
        context["destino"] = Destino.objects.get(pk=self.kwargs.get("desid"))
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.get_form_kwargs())
        if form.is_valid():
            form.instance.estado = "FD"
            form.instance.creador = self.request.user
            form.instance.destino_id = self.kwargs.get("desid")
            form.save()
        return self.render_to_response(context)


class MesaPartesMensajeriaImprimir(TemplateValidaLogin, DetailView):
    template_name = "tramite/mesapartes/mensajeria/imprimir.html"
    model = Destino
    context_object_name = "destino"


class MesaPartesMensajeriaImprimirPdfDirecto(TemplateValidaLogin, DetailView):
    template_name = "tramite/mesapartes/mensajeria/imprimirdirecto.html"
    model = Destino
    context_object_name = "destino"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        destino = self.object
        context = self.get_context_data(**kwargs)
        if hasattr(destino, "documentopdf"):
            docpdf = destino.documentopdf
        else:
            docpdf = destino.documento.documentoplantilla.documentopdf_set.first()
        docpdf.CrearRevision(request=request, impreso=True)
        context["datadoc"] = base64.b64encode(docpdf.pdffirma).decode('utf-8')
        return self.render_to_response(context=context)
