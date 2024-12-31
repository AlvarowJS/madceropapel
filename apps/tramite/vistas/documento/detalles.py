"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import json

import magic
import requests
from django.conf import settings
from django.db.models import ProtectedError, F, Value, CharField, Q
from django.db.models.functions import Concat, Cast
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from pytz import timezone as pytz_timezone
from django.views.generic import TemplateView
from rest_framework import views, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.models import Distrito, Cargo, PersonaJuridica
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.inicio.vistas.nucleo import ObtenerTokenNucleo
from apps.organizacion.models import PeriodoTrabajo, Area
from apps.tramite.formularios.documentodetalle import FormDestino, FormFirma, FormReferencia, FormAnexo, \
    FormAnexoFirma, FormAnexoImportar
from apps.tramite.models import Destino, TipoTramite, DocumentoFirma, DocumentoReferencia, DocumentoReferenciaOrigen, \
    DocumentoReferenciaModo, Expediente, TipoProveido, Anexo, AnexoFirma, Documento, DocumentoPDF, MensajeriaModoEntrega
from apps.tramite.vistas.documento.emitir import get_lista_anexos
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion


class DocumentoDestinoVista(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/detalles/destino.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        id = int(request.POST.get("codigo"))
        modo = request.POST.get("modo")
        desdetramite = request.POST.get("desdetramite")
        instance = None if id <= 0 else Destino.objects.get(pk=id)
        data = request.POST.copy()
        if not "mensajeriamodoentrega" in data:
            data["mensajeriamodoentrega"] = MensajeriaModoEntrega.objects.filter(estado=True).order_by("orden").first()
        if not "tipotramite" in data:
            data["tipotramite"] = TipoTramite.objects.get(codigo="0")
        if not "proveido" in data:
            proveido = 2 if desdetramite else 1
            data["proveido"] = TipoProveido.objects.filter(pk=proveido).first()
        if "periodotrabajo" in data and data["periodotrabajo"] != "":
            data["cargonombre"] = PeriodoTrabajo.objects.get(pk=data["periodotrabajo"]).CargoCorto()
        if "area" in data and data["area"] != "":
            area = Area.objects.get(pk=data["area"])
            data["dep"] = area.dependencia.codigo if not area.rindentepadre else area.rindentepadre.pk
            data["dependenciasiglas"] = area.dependencia.siglas if not area.rindentepadre else area.rindentepadre.siglas
        if "ubigeo" in data and data["ubigeo"] != "":
            ubigeo = int(data["ubigeo"])
            dist = Distrito.objects.get(pk=ubigeo)
            data["departamento"] = dist.provincia.departamento.pk
            data["provincia"] = dist.provincia.pk
        if data.get("personajuridica"):
            data["personajuridica"] = PersonaJuridica.objects.get(pk=data.get("personajuridica"))
        if data.get("tipodestinatario") == "PJ" and data.get("personajuridicatipo") == "O":
            data["personajuridicarz"] = data["personajuridica"]
            data["personajuridica"] = None
        else:
            data["personajuridicarz"] = None
        dependencia_area_prechoices = None
        if "dependencia" in data:
            dependencia_area_prechoices = [(data.get("dependencia_area"), data.get("dependencia_area_nombre"))]
            data["dependencia_responsable_texto"] = "%s - %s - %s" % (
                data.get("dependencia_responsable_dni"),
                data.get("dirigidoa"),
                data.get("cargo")
            )
        if "diasatencion" not in data:
            data["diasatencion"] = 0
        if not "tieneentregafisica" in data:
            data["entregafisica"] = ""
        fd = FormDestino(
            instance=instance, data=data, dependencia_area_prechoices=dependencia_area_prechoices,
            request=request
        )
        context["tipoDest"] = dict(Destino.TIPODESTINATARIO)[request.POST["tipodestinatario"]]
        context["form"] = fd
        context["modo"] = modo
        return self.render_to_response(context=context)


class DocumentoDestinoCargosVista(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/detalles/cargos.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        query = self.request.POST.get("query", "")
        cargos = Cargo.objects.order_by("nombrem")
        if len(query) > 0:
            cargos = cargos.filter(
                nombrem__icontains=query
            )
        context["cargos"] = cargos
        return self.render_to_response(context)


class DocumentoFirmaVista(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/detalles/firma.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        id = int(request.POST.get("codigo"))
        emi = int(request.POST.get("emi", 0))
        instance = None if id <= 0 else DocumentoFirma.objects.get(pk=id)
        data = request.POST.copy()
        ff = FormFirma(instance=instance, data=data)
        # fechaActual = timezone.localdate(timezone.now())
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        ff.fields["empleado"].queryset = ff.fields["empleado"].queryset.filter(
            activo=True,
            inicio__lte=fechaActual
        ).filter(
            Q(fin__gte=fechaActual)
            |
            Q(fin__isnull=True)
        )
        context["form"] = ff
        return self.render_to_response(context=context)


class DocumentoReferenciaVista(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/detalles/referencia.html"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        codigo = int(request.POST.get("codigo"))
        instance = None if codigo <= 0 else DocumentoReferencia.objects.get(pk=codigo)
        data = request.POST.copy()
        # Datos Initials
        if not data.get("origen"):
            data["origen"] = DocumentoReferenciaOrigen.objects.get(codigo="MCP")
        if not data.get("dependencia"):
            data["dependencia"] = request.user.persona.periodotrabajoactual(
                request.session.get("cambioperiodo")
            ).area.dependencia.pk
        data["modoref"] = DocumentoReferenciaModo.objects.get(pk=data.get("modoref", 1))
        # --------------
        oficinaprechoices = None
        documentotipoprechoices = None
        if data["modoref"].pideoficina and data.get("oficina"):
            oficinaprechoices = [(data.get("oficina"), data.get("oficinanombre"))]
        if data["modoref"].pidetipo and data.get("documentotipo"):
            documentotipoprechoices = [(data.get("documentotipo"), data.get("documentotiponombre"))]
        # --------------
        fr = FormReferencia(
            instance=instance, data=data, oficinaprechoices=oficinaprechoices,
            documentotipoprechoices=documentotipoprechoices
        )
        # --------------
        context["form"] = fr
        return self.render_to_response(context=context)


class DocumentoReferenciaPdfVista(views.APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        origen = self.kwargs.get("origen")
        nro = self.kwargs.get("nro")
        emi = self.kwargs.get("emi")
        dest = self.kwargs.get("dest")
        down = self.kwargs.get("down", 0)
        _response = None
        if origen == "SGD":
            token = ObtenerTokenNucleo()
            urlnucleo = settings.CONFIG_APP["NUCLEO"]["URL"]
            _docurl = "%s/%s" % (urlnucleo, settings.CONFIG_APP["NUCLEO"]["SGD"]["pdf"])
            _docurl = _docurl % (nro, emi)
            r = requests.post(
                _docurl,
                headers={
                    "Authorization": "Token " + token
                }
            )
            if r.ok:
                _response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/pdf'
                )
                nombre = r.headers["Content-Disposition"].split("filename=")[1]
                _response["Content-Disposition"] = "attachment; filename=%s" % nombre
                _response.write(r.text)
            else:
                _response = Response(
                    data={"msgerror": "No se pudo obtener el archivo adjunto"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif origen == "MCP":
            nrosep = nro.split("-")
            if nrosep[0] == settings.CONFIG_APP["Dependencia"]:
                _response = HttpResponse(
                    status=status.HTTP_200_OK,
                    content_type='application/pdf'
                )
                xDocPdf = None
                if emi != "0":
                    doc = Documento.objects.get(pk=int(emi))
                    docpdf = doc.documentoplantilla.documentopdf_set.filter(pdf__isnull=False).first()
                    if not docpdf:
                        docpdf = doc.documentoplantilla.contenido
                    else:
                        xDocPdf = docpdf
                        docpdf = docpdf.pdffirma or docpdf.pdf
                else:
                    doc = Expediente.objects.get(expedientenro=nro).documentos.order_by(
                        "creado"
                    ).first()
                    if dest == 0:
                        # docdes = doc.des_documento.filter("tipotramite__codigo", "creado").first()
                        docdes = doc.des_documento.exclude(ultimoestado__estado="AN").filter(
                            documentopdf__isnull=False
                        ).first()
                    else:
                        docdes = Destino.objects.filter(pk=dest).first()
                        doc = docdes.documento
                    if doc.origentipo in ["O", "P"]:
                        if hasattr(docdes, "documentopdf"):
                            xDocPdf = docdes.documentopdf
                            docpdf = docdes.documentopdf.pdffirma or docdes.documentopdf.pdf
                        else:
                            docpdf = docdes.documento.documentoplantilla.documentopdf_set.first()
                            xDocPdf = docpdf
                            docpdf = docpdf.pdffirma or docpdf.pdf
                    else:
                        if doc.documentotipoarea.documentotipo.esmultiple and \
                                not doc.documentotipoarea.documentotipo.esmultipledestino and \
                                doc.forma == "I":
                            xDocPdf = docdes.documentopdf
                            docpdf = docdes.documentopdf.pdf
                        else:
                            if docdes:
                                docpdf = docdes.documento.documentoplantilla.documentopdf_set.first()
                                if docpdf:
                                    xDocPdf = docpdf
                                    docpdf = docpdf.pdffirma or docpdf.pdf
                                    if not docpdf:
                                        xDocPdf.pdf = docdes.documento.documentoplantilla.contenido
                                        xDocPdf.save()
                                        docpdf = xDocPdf.pdf
                                else:
                                    docpdf = docdes.documento.documentoplantilla.contenido
                            else:
                                docpdf = doc.documentoplantilla.documentopdf_set.first()
                                if not docpdf and doc.origentipo in ["F", "V", "X", "C"]:
                                    docpdf = DocumentoPDF.objects.create(
                                        documentoplantilla=doc.documentoplantilla,
                                        destino=doc.des_documento.exclude(
                                            ultimoestado__estado="AN"
                                        ).order_by("pk").first(),
                                        pdf=doc.documentoplantilla.contenido,
                                        estado="G",
                                        creador_id=doc.creador_id
                                    )
                                xDocPdf = docpdf
                                docpdf = docpdf.pdffirma or docpdf.pdf
                                # docpdf = doc.documentoplantilla.contenido
                _response["Content-Disposition"] = "attachment; filename=%s" % doc.nombreDocumentoPdf()
                if xDocPdf:
                    xDocPdf.CrearRevision(request)
                if down == 0:
                    _response.write(base64.b64encode(docpdf).decode('utf-8'))
                else:
                    _response.write(docpdf)
            else:
                _response = Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            _response = Response(status=status.HTTP_400_BAD_REQUEST)
        return _response


class DocumentoAnexoAgregarVista(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/documento/detalles/anexo.html"
    model = Anexo
    form_class = FormAnexo

    def get_context_data(self, **kwargs):
        context = super(DocumentoAnexoAgregarVista, self).get_context_data(**kwargs)
        context["formFila"] = FormAnexoFirma()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.creador = self.request.user
            form.instance.documento_id = self.kwargs.get("pk")
            form.save()
            self.object = form.instance
            mimetype = magic.from_buffer(form.instance.archivo, mime=True)
            if mimetype == "application/pdf":
                firmadores = form.cleaned_data.get("firmadores", "") or "[]"
                firmadores = json.loads(firmadores)
                for firmador in firmadores:
                    formfirmador = FormAnexoFirma(data=firmador)
                    formfirmador.is_valid()
                    formfirmador.instance.anexo = form.instance
                    formfirmador.instance.creador = self.request.user
                    formfirmador.save()
            context["noBotonGuardar"] = True
            context["noBotonCancelar"] = True
            context["anxok"] = "El anexo se agregó correctamente!!"
            context["form"] = form
        return self.render_to_response(context)


class DocumentoAnexoEditarVista(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/detalles/anexo.html"
    model = Anexo
    form_class = FormAnexo

    def get_context_data(self, **kwargs):
        context = super(DocumentoAnexoEditarVista, self).get_context_data(**kwargs)
        context["formFila"] = FormAnexoFirma()
        firmadores = []
        for idx, firmador in enumerate(self.get_object().firmadores.order_by("pk")):
            formfirmador = FormAnexoFirma(data={
                "codigo": firmador.pk,
                "modo": firmador.modo,
                "empleado": firmador.empleado
            })
            formfirmador.fields["codigo"].widget.attrs["id"] = "id_codigo_%s" % idx
            formfirmador.fields["modo"].widget.attrs["id"] = "id_modo_%s" % idx
            formfirmador.fields["empleado"].widget.attrs["id"] = "id_empleado_%s" % idx
            firmadores.append(formfirmador)
        context["firmadores"] = firmadores
        context["botonguardartexto"] = "Actualizar"
        return context

    def get_form(self, form_class=None):
        form = super(DocumentoAnexoEditarVista, self).get_form(form_class)
        firmadores = list(self.get_object().firmadores.order_by("pk").annotate(
            codigo=F("pk")
        ).values(
            "codigo", "empleado_id", "modo"
        ))
        for firmador in firmadores:
            firmador["empleado"] = firmador["empleado_id"]
            del firmador["empleado_id"]
        form.fields["firmadores"].initial = json.dumps(firmadores, ensure_ascii=False)
        if form.instance.provienede:
            del form.fields["archivof"]
            del form.fields["descripcion"]
        else:
            form.fields["archivof"].required = False
        return form

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        if form.is_valid():
            archivo = form.instance.archivo
            form.instance.editor = self.request.user
            form.save()
            self.object = form.instance
            mimetype = magic.from_buffer(archivo, mime=True)
            firmadoresids = []
            cambios = False
            if mimetype == "application/pdf":
                firmadores = json.loads(form.cleaned_data.get("firmadores", "[]"))
                for firmador in firmadores:
                    anexofirma = AnexoFirma.objects.filter(pk=firmador["codigo"]).first()
                    instancia = AnexoFirma.objects.filter(pk=firmador["codigo"]).first()
                    firmador["empleado"] = PeriodoTrabajo.objects.get(pk=int(firmador["empleado"]))
                    formfirmador = FormAnexoFirma(data=firmador, instance=instancia)
                    if formfirmador.is_valid():
                        if formfirmador.instance.is_dirty():
                            formfirmador.instance.estado = "SF"
                        if not instancia:
                            formfirmador.instance.creador = self.request.user
                            formfirmador.instance.anexo = form.instance
                        else:
                            formfirmador.instance.editor = self.request.user
                            if anexofirma.estado == "FI" and formfirmador.instance.estado == "SF":
                                cambios = True
                        formfirmador.save()
                        firmadoresids.append(formfirmador.instance.pk)
                    else:
                        print(formfirmador.errors)
            firmasdele = self.object.firmadores.exclude(pk__in=firmadoresids)
            if firmasdele.filter(estado="FI").count() > 0:
                cambios = True
            firmasdele.delete()
            if cambios:
                self.object.archivofirmado = None
                self.object.save()
                AnexoFirma.objects.filter(pk__in=firmadoresids).update(estado="SF")
            context["noBotonGuardar"] = True
            context["noBotonCancelar"] = True
            context["anxok"] = "El anexo se actualizó correctamente!!"
            context["form"] = form
        return self.render_to_response(context)


class DocumentoAnexoQuitarVista(TemplateValidaLogin, VistaEliminacion):
    template_name = "tramite/documento/detalles/anexoquitar.html"
    model = Anexo

    def get_context_data(self, **kwargs):
        _result = super(DocumentoAnexoQuitarVista, self).get_context_data(**kwargs)
        _result["botonguardartexto"] = "Quitar"
        return _result

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        try:
            context["anxok"] = self.object.documento.pk
            context["noBotonGuardar"] = True
            context["noBotonCancelar"] = True
            self.object.firmadores.all().delete()
            self.object.revisiones.all().delete()
            self.object.delete()
            _result = self.render_to_response(context)
        except ProtectedError as e:
            context["errordelete"] = "El anexo no puede ser eliminado"
            _result = self.render_to_response(context)
        return _result


class DocumentoAnexoImportarVista(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/documento/detalles/anexoimportar.html"
    model = DocumentoReferencia
    form_class = FormAnexoImportar

    def get_form(self, form_class=None):
        form = super(DocumentoAnexoImportarVista, self).get_form(form_class)
        dref = self.get_object()
        if dref.origen.codigo in ["MCP"]:
            anxsel = "["
            for anx in dref.destino.documento.anexos.order_by("id"):
                anxsel += str(anx.id) + ","
            form.fields["listaanexos"].initial = anxsel[:-1] + "]"
        return form

    def get_context_data(self, **kwargs):
        context = super(DocumentoAnexoImportarVista, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Importar"
        dref = self.get_object()
        token = self.request.user.auth_token.key
        urldown = reverse_lazy("apptra:documento_anexo_descargar", kwargs={"pk": 0})
        urldown = urldown.replace("0", "")
        if dref.origen.codigo in ["MCP"]:
            context["anexos"] = dref.destino.documento.anexos.order_by("id").annotate(
                archivourl=Concat(
                    Value("viewPDF('"),
                    Value(urldown),
                    Cast(F("pk"), CharField()),
                    Value("', '"),
                    F("archivonombre"),
                    Value("', '"),
                    Value(token),
                    Value("')")
                )
            )
            if context["anexos"].count() == 0:
                context["noBotonGuardar"] = True
        else:
            context["noBotonGuardar"] = True
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        if form.is_valid():
            cldt = form.cleaned_data
            listaanexos = eval(cldt["listaanexos"])
            if len(listaanexos) > 0:
                for anexoold in Anexo.objects.filter(pk__in=listaanexos).order_by("pk"):
                    anexoold.provienede_id = anexoold.pk
                    anexoold.pk = None
                    anexoold.documento = self.get_object().documento
                    anexoold.save()
                context["anxok"] = self.get_object().documento.pk
            else:
                form.add_error(None, "Debe elegir al menos 01 Anexo")
            context["form"] = form
        return self.render_to_response(context)


class DocumentoAnexoDescargarVista(views.APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        anx = Anexo.objects.filter(pk=pk).first()
        enbase64 = request.headers.get("Base64", "false").lower()
        if anx:
            filepdf = anx.archivofirmado or anx.archivo
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type=magic.from_buffer(filepdf, mime=True)
            )
            response["Content-Disposition"] = "attachment; filename=%s" % anx.archivonombre
            if enbase64 == "true":
                response.write(base64.b64encode(filepdf).decode('utf-8'))
            else:
                response.write(filepdf)
            anx.CrearRevision(request)
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class DocumentoAnexoListarVista(TemplateValidaLogin, TemplateView):
    template_name = "campos/blank.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def render_to_response(self, context, **response_kwargs):
        _result = []
        doc = Documento.objects.filter(pk=self.kwargs.get("pk")).first()
        if doc:
            _result = get_lista_anexos(doc, self.request)
        return JsonResponse(_result, safe=False)
