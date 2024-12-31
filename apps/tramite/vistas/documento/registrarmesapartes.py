"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import json

from django.db.models import F, Value, Case, When, CharField, ProtectedError, BooleanField
from django.db.models.functions import Cast, Concat
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, DetailView
from rest_framework import views, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.models import TipoDocumentoIdentidad, Persona, PersonaJuridica, Pais
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.models import PeriodoTrabajo
from apps.sockets.vistas.mensajes import SocketMsg
from apps.tramite.formularios.documentodetalle import FormDestino, FormAnexo
from apps.tramite.formularios.mesapartesregistrar import MesaPartesRegistrarForm, MesaPartesRegistrarDestinosForm, \
    MesaPartesRegistrarArchivosForm, MesaPartesEmitirForm
from apps.tramite.models import Documento, DocumentoEstado, Destino, DocumentoPDF, DocumentoPlantilla, DestinoEstado, \
    Anexo, DestinoEstadoMensajeria, MensajeriaModoEntrega
from apps.tramite.vistas.documento.emitir import get_lista_destinos
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion


def GuardarRemitente(form, request):
    cldt = form.cleaned_data
    # Validamos los datos del Tipo de Remitente
    persona = None
    if cldt["remitentetipo"] in ["C", "J"]:
        if cldt["ciudadanoemisortipo"].codigo != "OTR":
            persona = Persona.objects.filter(
                tipodocumentoidentidad=cldt["ciudadanoemisortipo"],
                numero=cldt["ciudadanoemisordni"] if cldt["ciudadanoemisortipo"].codigo == "DNI" else
                cldt["ciudadanoemisornumero"]
            ).first()
        else:
            persona = Persona.objects.filter(
                tipodocumentoidentidad=cldt["ciudadanoemisortipo"],
                paterno__iexact=cldt["ciudadanoemisorpaterno"],
                materno__iexact=cldt["ciudadanoemisormaterno"],
                nombres__iexact=cldt["ciudadanoemisornombres"]
            ).first()
        if not persona:
            persona = Persona(
                tipodocumentoidentidad=cldt["ciudadanoemisortipo"],
                ubigeo=cldt["distrito"],
                pais=cldt["distrito"].provincia.departamento.pais,
                direccion=cldt["direccion"],
                telefono=cldt["telefono"],
                correo=cldt["correo"],
                confirmado=True,
                creador=request.user
            )
        if cldt["ciudadanoemisortipo"].codigo != "OTR":
            persona.numero = cldt["ciudadanoemisordni"] if cldt["ciudadanoemisortipo"].codigo == "DNI" else \
                cldt["ciudadanoemisornumero"]
        if cldt["ciudadanoemisortipo"].codigo != "DNI":
            persona.paterno = cldt.get("ciudadanoemisorpaterno", "").upper()
            persona.materno = cldt.get("ciudadanoemisormaterno", "").upper()
            persona.nombres = cldt.get("ciudadanoemisornombres", "").upper()
            persona.sexo = "M" if cldt["ciudadanoemisorsexo"] else "F"
        if cldt["remitentetipo"] == "C":
            persona.ubigeo = cldt["distrito"]
            persona.direccion = cldt["direccion"]
            persona.telefono = cldt["telefono"]
            persona.correo = cldt["correo"]
        persona.save()
        form.instance.ciudadanoemisor = persona
    if cldt["remitentetipo"] == "J":
        if cldt["personajuridicatipo"] == "O":
            pj = PersonaJuridica.objects.filter(
                ruc__startswith="O",
                razonsocial__iexact=cldt["personajuridicarz"]
            ).first()
            if not pj:
                pj = PersonaJuridica(
                    tipo="O",
                    razonsocial=cldt["personajuridicarz"],
                    creador=request.user,
                    pais_id=48
                )
        else:
            pj = PersonaJuridica.objects.filter(
                ruc=cldt["personajuridicaruc"],
                tipo="R"
            ).first()
        pj.representante = persona
        pj.representantecargo = cldt["ciudadanocargo"]
        pj.ubigeo = cldt["distrito"]
        pj.direccion = cldt["direccion"]
        pj.telefono = cldt["telefono"]
        pj.correo = cldt["correo"]
        pj.save()
        form.instance.personajuridica = pj


class MesaPartesRegistrar(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/mesapartes/registrar/registrar.html"
    model = Documento
    form_class = MesaPartesRegistrarForm

    def get_form(self, form_class=None):
        form = super(MesaPartesRegistrar, self).get_form(form_class)
        form.fields["ciudadanoemisortipo"].initial = TipoDocumentoIdentidad.objects.filter(codigo="DNI").first()
        form.fields["documentotipoarea"].queryset = form.fields["documentotipoarea"].queryset.filter(
            area=self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area,
            documentotipo__usoexterno=True
        )
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesRegistrar, self).get_context_data(**kwargs)
        if self.request.POST:
            self.template_name = "tramite/mesapartes/registrar/registrar_form.html"
        context["se_puede_editar"] = True
        return context

    def form_valid(self, form):
        if form.is_valid():
            form.instance.origentipo = "F"
            form.instance.emisor = self.request.user.persona.periodotrabajoactual(
                self.request.session.get("cambioperiodo")
            )
            form.instance.creador = self.request.user
            GuardarRemitente(form, self.request)
            super(MesaPartesRegistrar, self).form_valid(form)
            context = self.get_context_data(form=form)
            doc = Documento.objects.get(pk=form.instance.pk)
            cldt = form.cleaned_data
            # 01 - Guardamos los des+tinos
            idsdestinos = []
            destinos = cldt.get("destinos", "[]")
            if len(destinos) == 0:
                destinos = "[]"
            destinos = json.loads(destinos)
            for destino in destinos:
                fdest = FormDestino(data=destino, request=self.request)
                if not destino.get("mensajeriamodoentrega"):
                    fdest.instance.mensajeriamodoentrega = MensajeriaModoEntrega.objects.filter(
                        estado=True
                    ).order_by("orden").first()
                if fdest.is_valid():
                    fdest.instance.documento = doc
                    fdest.instance.creador = self.request.user
                    fdest.save()
                    idsdestinos.append({
                        "idold": int(destino["codigo"]),
                        "idnew": fdest.instance.pk
                    })
            context["idsdestinos"] = idsdestinos
            # Guardamos el Archivo PDF
            if cldt.get("contenido"):
                docplla = doc.documentoplantilla
                docplla.contenido = cldt.get("contenido").read()
                docplla.save()
                # Verificamos si se emite
                if len(destinos) > 0:
                    docest = DocumentoEstado(
                        estado="EM",
                        creador=self.request.user,
                        documento=doc,
                        firmado=False
                    )
                    docest.save()
                    for destino in doc.des_documento.exclude(ultimoestado__estado="AN"):
                        DestinoEstado.objects.create(
                            destino=destino,
                            estado="NL",
                            creador=self.request.user
                        )
            template = get_template("tramite/mensajes/externo/registrado.html")
            context["doc"] = doc
            context["okmsg"] = template.render(request=self.request, context=context)
            context["privez"] = True
            # Notificamos al cliente
            SocketMsg(
                userid=self.request.user.id,
                funcpost='refrescarTabla("tablaMesaPartesRegistrados")'
            )
            result = self.render_to_response(context)
        else:
            result = self.render_to_response(self.get_context_data(form=form))
        return result

    def form_invalid(self, form):
        fi = super(MesaPartesRegistrar, self).form_invalid(form)
        print(form.errors)
        return fi


class MesaPartesRegistrarEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/registrar/registrar.html"
    model = Documento
    form_class = MesaPartesRegistrarForm

    def get_initial(self):
        initial = super(MesaPartesRegistrarEditar, self).get_initial()
        doc = self.object
        if doc.ciudadanoemisor:
            initial["ciudadanoemisortipo"] = doc.ciudadanoemisor.tipodocumentoidentidad
            if doc.ciudadanoemisor.tipodocumentoidentidad.codigo == "DNI":
                initial["ciudadanoemisordni"] = doc.ciudadanoemisor.numero
            else:
                initial["ciudadanoemisorpaterno"] = doc.ciudadanoemisor.paterno
                initial["ciudadanoemisormaterno"] = doc.ciudadanoemisor.materno
                initial["ciudadanoemisornombres"] = doc.ciudadanoemisor.nombres
                initial["ciudadanoemisorsexo"] = (doc.ciudadanoemisor.sexo == "M")
            if doc.ciudadanoemisor.tipodocumentoidentidad.codigo in ["CET", "PAS"]:
                initial["ciudadanoemisornumero"] = doc.ciudadanoemisor.numero
                initial["ciudadanoemisorcodigo"] = doc.ciudadanoemisor.pk
        if doc.remitentetipo == "J":
            if doc.personajuridica.tipo == "R":
                initial["personajuridicaruc"] = doc.personajuridica.ruc
            else:
                initial["personajuridicarz"] = doc.personajuridica.razonsocial
        if doc.ciudadanotramitador:
            initial["ciudadanotramitadordni"] = doc.ciudadanotramitador.numero
        destinos = get_lista_destinos(doc)
        initial["destinos"] = json.dumps(destinos, ensure_ascii=False)
        return initial

    def get_form(self, form_class=None):
        form = super(MesaPartesRegistrarEditar, self).get_form(form_class)
        form.fields["documentotipoarea"].queryset = form.fields["documentotipoarea"].queryset.filter(
            area=self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo")).area,
            documentotipo__usoexterno=True
        )
        return form

    def get_context_data(self, **kwargs):
        context = super(MesaPartesRegistrarEditar, self).get_context_data(**kwargs)
        if self.request.POST:
            self.template_name = "tramite/mesapartes/registrar/registrar_form.html"
        if self.object.ultimoestado.estado == "RE" and (
                self.object.creador == self.request.user or
                self.object.responsable == self.request.user.persona.periodotrabajoactual(
            self.request.session.get("cambioperiodo"))
        ):
            context["se_puede_editar"] = True
        return context

    def form_valid(self, form):
        if form.is_valid():
            GuardarRemitente(form, self.request)
            super(MesaPartesRegistrarEditar, self).form_valid(form)
            doc = Documento.objects.get(pk=form.instance.pk)
            # 01 - Guardamos los destinos
            idsEditados = []
            idsdestinos = []
            destinos = form.cleaned_data.get("destinos", "[]")
            if len(destinos) == 0:
                destinos = "[]"
            destinos = json.loads(destinos)
            for destino in destinos:
                codigo = int(destino["codigo"])
                instance = None
                if codigo > 0:
                    instance = Destino.objects.get(pk=codigo)
                fdest = FormDestino(data=destino, instance=instance, request=self.request)
                if not destino.get("mensajeriamodoentrega"):
                    fdest.instance.mensajeriamodoentrega = MensajeriaModoEntrega.objects.filter(
                        estado=True
                    ).order_by("orden").first()
                if fdest.is_valid():
                    esnuevo = False
                    if not fdest.instance.pk:
                        esnuevo = True
                        fdest.instance.documento = doc
                        fdest.instance.creador = self.request.user
                    else:
                        fdest.instance.editor = self.request.user
                    fdest.save()
                    idsEditados.append(fdest.instance.pk)
                    if esnuevo:
                        idsdestinos.append({
                            "idold": codigo,
                            "idnew": fdest.instance.pk
                        })
                else:
                    print(fdest.instance.pk, fdest.errors)
            for desdel in doc.des_documento.exclude(ultimoestado__estado="AN").exclude(pk__in=idsEditados):
                desdel.ultimoestado = None
                desdel.save()
                desdel.destinoestados.all().delete()
                if hasattr(desdel, "documentopdf"):
                    desdel.documentopdf.revisiones.all().delete()
                    desdel.documentopdf.tokens.all().delete()
                    desdel.documentopdf.delete()
                desdel.delete()
            if doc.documentoplantilla.documentopdf_set.count() == 0 and doc.des_documento.count() > 0:
                if doc.documentoplantilla.contenido:
                    DocumentoPDF.objects.create(
                        documentoplantilla=doc.documentoplantilla,
                        destino=doc.des_documento.order_by("pk").first(),
                        pdf=doc.documentoplantilla.contenido,
                        creador=self.request.user
                    )
            context = self.get_context_data(form=form)
            context["idsdestinos"] = idsdestinos
            context["documento"] = doc
            context["okmsg"] = True
            # Notificamos al cliente
            SocketMsg(
                userid=self.request.user.id,
                funcpost='refrescarTabla("tablaMesaPartesRegistrados")',
                tipo='primary',
                clase='bg-primary',
                titulo="Correcto",
                mensaje="Los datos se guardaron correctamente"
            )
            result = self.render_to_response(context)
        else:
            print(form.errors)
            result = self.render_to_response(self.get_context_data(form=form))
        return result

    def form_invalid(self, form):
        fi = super(MesaPartesRegistrarEditar, self).form_invalid(form)
        print(form.errors)
        return fi


class MesaPartesRegistrarDestinos(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/destinos/vista.html"
    model = Documento
    form_class = MesaPartesRegistrarDestinosForm

    def get_form(self, form_class=None):
        form = super(MesaPartesRegistrarDestinos, self).get_form(form_class)
        form.fields["destinosmp"].initial = json.dumps(get_lista_destinos(self.object), ensure_ascii=False)
        return form

    def form_valid(self, form):
        if form.is_valid():
            doc = self.get_object()
            context = self.get_context_data(form=form)
            cldt = form.cleaned_data
            # Guardamos los Destinos
            destinos = json.loads(cldt["destinosmp"])
            idsEditados = []
            for destino in destinos:
                codigo = int(destino["codigo"])
                instance = None
                if codigo > 0:
                    instance = Destino.objects.get(pk=codigo)
                fdest = FormDestino(data=destino, instance=instance, request=self.request)
                if not destino.get("mensajeriamodoentrega"):
                    fdest.instance.mensajeriamodoentrega = MensajeriaModoEntrega.objects.filter(
                        estado=True
                    ).order_by("orden").first()
                if fdest.is_valid():
                    grabar = True
                    if not fdest.instance.pk:
                        fdest.instance.documento = doc
                        fdest.instance.creador = self.request.user
                    else:
                        fdest.instance.editor = self.request.user
                        if not fdest.instance.ultimoestado.estado in ["NL", "LE", "RG", "RH"]:
                            grabar = False
                    if grabar:
                        fdest.save()
                        if fdest.instance.ultimoestado.estado == "RH":
                            DestinoEstado.objects.create(
                                destino=fdest.instance,
                                observacion=destino["obsnew"],
                                estado="NL" if fdest.instance.documento.estadoemitido else "RG",
                                creador=self.request.user
                            )
                        if fdest.instance.ultimoestado.estado == "RG" and fdest.instance.documento.estadoemitido:
                            DestinoEstado.objects.create(
                                destino=fdest.instance,
                                estado="NL",
                                creador=self.request.user
                            )
                        if doc.documentotipoarea.documentotipo.esmultiple and not \
                                doc.documentotipoarea.documentotipo.esmultipledestino:
                            if not hasattr(fdest.instance, "documentopdf"):
                                DocumentoPDF.objects.create(
                                    documentoplantilla=doc.documentoplantilla,
                                    destino=fdest.instance,
                                    pdf=doc.documentoplantilla.contenido,
                                    estado="G",
                                    creador=self.request.user
                                )
                    idsEditados.append(fdest.instance.pk)
                else:
                    if fdest.instance.pk:
                        idsEditados.append(fdest.instance.pk)
                    if fdest.errors.get("periodotrabajo"):
                        pt = PeriodoTrabajo.objects.get(pk=destino["periodotrabajo"])
                        form.add_error(
                            None,
                            "El destino %s ya no está disponible" % pt.persona.apellidocompleto
                        )
            if not form.errors:
                for desdel in doc.des_documento.exclude(ultimoestado__estado="AN").exclude(pk__in=idsEditados):
                    if desdel.ultimoestado.estado == "RH":
                        DestinoEstado.objects.create(
                            destino=desdel,
                            estado="AN",
                            creador=self.request.user
                        )
                    else:
                        if desdel.destinoreferencias.count() > 0:
                            DestinoEstado.objects.create(
                                destino=desdel,
                                estado="AN",
                                creador=self.request.user
                            )
                        else:
                            desdel.ultimoestado = None
                            desdel.save()
                            desdel.destinoestados.all().delete()
                            if hasattr(desdel, "documentopdf"):
                                docpdf = desdel.documentopdf
                                docpdf.revisiones.all().delete()
                                docpdf.tokens.all().delete()
                                docpdf.delete()
                            desdel.delete()
                if not doc.documentotipoarea.documentotipo.esmultiple:
                    if doc.des_documento.exclude(ultimoestado__estado="AN").count() > 0 and \
                            doc.documentoplantilla.documentopdf_set.exclude(
                                destino__ultimoestado__estado="AN"
                            ).count() == 0:
                        DocumentoPDF.objects.create(
                            documentoplantilla=doc.documentoplantilla,
                            destino=doc.des_documento.exclude(ultimoestado__estado="AN").order_by("pk").first(),
                            pdf=doc.documentoplantilla.contenido,
                            estado="G",
                            creador=self.request.user
                        )
                if doc.des_documento.exclude(ultimoestado__estado="AN").count() == 0:
                    doc.ultimoestado = doc.documentoestado_set.filter(estado="RE").order_by("-creado").first()
                    doc.estadoemitido = None
                    doc.save()
                SocketMsg(
                    tipo='primary',
                    clase='bg-primary',
                    titulo='Correcto',
                    userid=self.request.user.pk,
                    funcpost='refrescarTabla("tablaMesaPartesRegistrados", "#modal-principal-centro")',
                    mensaje="Los destinos se actualizaron correctamente!!"
                )
            context["form"] = form
            result = self.render_to_response(context)
        else:
            result = self.render_to_response(self.get_context_data(form=form))
        return result


class MesaPartesRegistrarArchivos(TemplateValidaLogin, TemplateView):
    template_name = "tramite/mesapartes/archivos/vista.html"
    extra_context = {
        "noBotonGuardar": True,
        "noBotonCancelar": True
    }

    def get_context_data(self, **kwargs):
        context = super(MesaPartesRegistrarArchivos, self).get_context_data(**kwargs)
        context["maxfiles"] = 1
        doc = Documento.objects.get(pk=self.kwargs.get("pk"))
        context["doc"] = doc
        if doc.documentotipoarea.documentotipo.esmultiple:
            context["maxfiles"] = doc.des_documento.exclude(ultimoestado__estado="AN").count()
        return context


def MesaPartesRegistrarArchivosSubir(request, iddoc):
    _result = dict()
    _result["nothing"] = False
    if request.method == "POST":
        doc = Documento.objects.filter(pk=iddoc).first()
        if doc:
            archivo = request.FILES["docarchivos"]
            datafile = archivo.read()
            if doc.documentotipoarea.documentotipo.esmultiple:
                iddest = int(request.POST.get("destino"))
                destino = doc.des_documento.filter(pk=iddest).first()
                if not hasattr(destino, "documentopdf"):
                    DocumentoPDF.objects.create(
                        documentoplantilla=doc.documentoplantilla,
                        destino=destino,
                        pdf=datafile,
                        estado="G",
                        creador=request.user
                    )
                else:
                    docpdf = destino.documentopdf
                    docpdf.pdf = datafile
                    docpdf.editor = request.user
                    docpdf.save()
            else:
                if not hasattr(doc, "documentoplantilla"):
                    docplla = DocumentoPlantilla(
                        documento=doc,
                        creador=request.user
                    )
                else:
                    docplla = doc.documentoplantilla
                    docplla.editor = request.user
                    for docpdf in docplla.documentopdf_set.all():
                        docpdf.pdf = datafile
                        docpdf.save()
                docplla.contenido = datafile
                docplla.save()
            _result["nothing"] = True
    return JsonResponse(_result)


class MesaPartesVerDocumento(views.APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        iddest = self.kwargs.get("iddest")
        destino = Destino.objects.filter(pk=iddest).first()
        if destino:
            nombre = destino.documento.nombreDocumentoNumero()
            if destino.documento.documentotipoarea.documentotipo.esmultiple:
                docpdf = destino.documentopdf.pdf
                nombre += "_%s" % (list(
                    destino.documento.des_documento.exclude(
                        ultimoestado__estado="AN"
                    ).order_by("pk").values_list("pk", flat=True)
                ).index(iddest) + 1)
            else:
                docpdf = destino.documento.documentoplantilla.contenido
            nombre += ".pdf"
            response = HttpResponse(
                status=status.HTTP_200_OK,
                content_type='application/pdf'
            )
            response["Content-Disposition"] = "inline; filename=%s" % nombre
            response.write(docpdf)
            # response.write(base64.b64encode(docpdf).decode('utf-8'))
            return response
        return Response([], status=status.HTTP_400_BAD_REQUEST)


class MesaPartesRegistrarBotones(TemplateValidaLogin, DetailView):
    template_name = "tramite/mesapartes/registrar/botones/_botones.html"
    http_method_names = "post"
    model = Documento

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context["formid"] = request.POST.get("formid")
        # context["tab"] = request.POST.get("tab")
        # context["tabid"] = request.POST.get("tabid")
        context["cf"] = False if request.POST.get("cf", "false") == "false" else True
        return self.render_to_response(context)


def EmitirMesaDePartes(doc, request):
    for destino in doc.des_documento.exclude(ultimoestado__estado="AN"):
        if destino.tipodestinatario == "UO":
            if destino.periodotrabajo.persona.usuario:
                SocketMsg(
                    tipo='primary',
                    clase='bg-danger',
                    userid=destino.periodotrabajo.persona.usuario.pk,
                    titulo='Bandeja de Entrada',
                    mensaje='%s, %s' % (
                        "Hola %s" % destino.periodotrabajo.persona.nombres,
                        "le han remitido un expediente desde Trámite Documentario."
                    ),
                    funcpost='refrescarTableros("dbEntrada", true)'
                )
        if destino.ultimoestado.estado != "NL":
            DestinoEstado.objects.create(destino=destino, estado="NL", creador=request.user)
    if doc.ultimoestado.estado != "EM":
        DocumentoEstado.objects.create(documento=doc, estado="EM", firmado=True, creador=request.user)
        doc.editor = request.user
        doc.actualizado = timezone.now()
        doc.save()


class MesaPartesRegistrarEmitir(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/registrar/emitir.html"
    model = Documento
    form_class = MesaPartesEmitirForm
    extra_context = {
        "botonguardartexto": "Emitir"
    }

    def form_valid(self, form):
        if form.is_valid():
            result = super(MesaPartesRegistrarEmitir, self).form_valid(form)
            # context = self.get_context_data(form=form)
            doc = Documento.objects.get(pk=form.instance.pk)
            # Notificamos a los Destinos
            EmitirMesaDePartes(doc, self.request)
            # Notificamos al cliente
            SocketMsg(
                userid=self.request.user.id,
                funcpost='',
                tipo='primary',
                clase='bg-primary',
                titulo="Correcto",
                mensaje="El expediente se emitió correctamente"
            )
        else:
            print(form.errors)
            result = self.render_to_response(self.get_context_data(form=form))
        return result

    def form_invalid(self, form):
        fi = super(MesaPartesRegistrarEmitir, self).form_invalid(form)
        print(form.errors)
        return fi


class MesaPartesRegistrarEmitirAnular(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/registrar/emitiranular.html"
    model = Documento
    form_class = MesaPartesEmitirForm
    extra_context = {
        "botonguardartexto": "Anular Emisión"
    }

    def form_valid(self, form):
        if form.is_valid():
            result = super(MesaPartesRegistrarEmitirAnular, self).form_valid(form)
            # context = self.get_context_data(form=form)
            doc = Documento.objects.get(pk=form.instance.pk)
            # Notificamos a los Destinos
            if doc.ultimoestado.estado == "EM":
                for destino in doc.des_documento.exclude(ultimoestado__estado="AN"):
                    if destino.tipodestinatario == "UO":
                        if destino.periodotrabajo.persona.usuario:
                            SocketMsg(
                                userid=destino.periodotrabajo.persona.usuario.pk,
                                funcpost='refrescarTableros("dbEntrada", true)'
                            )
                    if destino.ultimoestado.estado != "NL":
                        DestinoEstado.objects.create(destino=destino, estado="NL", creador=self.request.user)

                DocumentoEstado.objects.create(documento=doc, estado="RE", firmado=False, creador=self.request.user)
            # Notificamos al cliente
            SocketMsg(
                userid=self.request.user.id,
                funcpost='refrescarTabla("tablaMesaPartesRegistrados", "#modal-principal-centro")',
                tipo='primary',
                clase='bg-primary',
                titulo="Correcto",
                mensaje="Se anuló la Emisión del Expediente correctamente"
            )
        else:
            print(form.errors)
            result = self.render_to_response(self.get_context_data(form=form))
        return result

    def form_invalid(self, form):
        fi = super(MesaPartesRegistrarEmitirAnular, self).form_invalid(form)
        print(form.errors)
        return fi


class MesaPartesRegistrarEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "tramite/mesapartes/registrar/eliminar.html"
    model = Documento
    extra_context = {
        "botonguardartexto": "Eliminar Expediente"
    }

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        # try:
        doc = self.get_object()
        if hasattr(doc, 'documentoplantilla'):
            for docpdf in doc.documentoplantilla.documentopdf_set.all():
                docpdf.revisiones.all().delete()
                docpdf.tokens.all().delete()
            doc.documentoplantilla.documentopdf_set.all().delete()
            doc.documentoplantilla.delete()
        doc.des_documento.all().update(ultimoestado=None, ultimoestadomensajeria=None)
        DestinoEstadoMensajeria.objects.filter(destino__documento=doc).delete()
        DestinoEstado.objects.filter(destino__documento=doc).delete()
        doc.des_documento.all().delete()
        for anexo in doc.anexos.all():
            anexo.firmadores.all().delete()
            anexo.revisiones.all().delete()
        doc.anexos.all().delete()
        doc.ultimoestado = None
        doc.estadoemitido = None
        doc.expediente = None
        doc.save()
        doc.documentoestado_set.all().delete()
        if doc.expediente.documentos.count() == 0:
            exp = doc.expediente
            exp.delete()
        _result = super(MesaPartesRegistrarEliminar, self).form_valid(form)
        return _result


class MesaPartesRegistrarAnexos(TemplateValidaLogin, DetailView):
    template_name = "tramite/mesapartes/anexos/vista.html"
    extra_context = {
        "noBotonGuardar": True,
        "noBotonCancelar": True
    }
    model = Documento
    context_object_name = "doc"

    def get_context_data(self, **kwargs):
        context = super(MesaPartesRegistrarAnexos, self).get_context_data(**kwargs)
        context["urleditarcustom"] = reverse_lazy("apptra:mesapartes_registrar_anexo_editar", kwargs={"pk": 0})
        context["urleliminarcustom"] = reverse_lazy("apptra:mesapartes_registrar_anexo_quitar", kwargs={"pk": 0})
        context["anexos"] = list(self.object.anexos.order_by("pk").annotate(
            editar=Value(1),
            codigo=F("id")
        ).values(
            "codigo", "descripcion", "archivonombre", "editar"
        ))
        return context


class MesaPartesRegistrarAnexoAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "tramite/mesapartes/anexos/agregar.html"
    model = Anexo
    form_class = FormAnexo

    def get_context_data(self, **kwargs):
        context = super(MesaPartesRegistrarAnexoAgregar, self).get_context_data(**kwargs)
        context["doc"] = Documento.objects.get(pk=self.kwargs.get("pk"))
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.instance.creador = self.request.user
            form.instance.documento_id = self.kwargs.get("pk")
            form.save()
            context["anxok"] = True
            context["form"] = form
        return self.render_to_response(context)


class MesaPartesRegistrarAnexoEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "tramite/mesapartes/anexos/agregar.html"
    model = Anexo
    form_class = FormAnexo

    def get_context_data(self, **kwargs):
        context = super(MesaPartesRegistrarAnexoEditar, self).get_context_data(**kwargs)
        context["doc"] = self.object.documento
        return context

    def get_form(self, form_class=None):
        form = super(MesaPartesRegistrarAnexoEditar, self).get_form(form_class)
        form.fields["archivof"].required = False
        return form

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        if form.is_valid():
            archivo = form.instance.archivo
            form.instance.editor = self.request.user
            form.save()
            self.object = form.instance
            context["anxok"] = True
            context["form"] = form
        return self.render_to_response(context)


class MesaPartesRegistrarAnexoQuitar(TemplateValidaLogin, VistaEliminacion):
    template_name = "tramite/mesapartes/anexos/quitar.html"
    model = Anexo

    def get_context_data(self, **kwargs):
        _result = super(MesaPartesRegistrarAnexoQuitar, self).get_context_data(**kwargs)
        _result["botonguardartexto"] = "Quitar"
        return _result

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        try:
            context["doc"] = self.object.documento
            self.object.delete()
            context["anxok"] = True
            _result = self.render_to_response(context)
        except ProtectedError as e:
            context["errordelete"] = "El anexo no puede ser eliminado"
            _result = self.render_to_response(context)
        return _result
