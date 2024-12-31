"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.models import TipoDocumentoIdentidad, Persona
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.trabajador import FormPeriodoTrabajo
from apps.tramite.formularios.documentodetalle import FormDestino
from apps.tramite.formularios.mesapartesregistrar import MesaPartesRegistrarForm
from apps.tramite.models import Documento, Destino
from apps.tramite.vistas.varios import ConsultarDNI


class ConsultaDniTrabajador(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/dnitrabajador.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        dni = request.POST.get("dni")
        per, estado = ConsultarDNI(dni, request)
        if estado:
            context["message"] = estado
            context["success"] = False
        else:
            context["per"] = per
            context["success"] = True
        # fd = FormPeriodoTrabajo(data={
        #     "persona": None if not per else per.pk
        # })
        # context["estado"] = estado
        # context["form"] = fd
        return self.render_to_response(context=context)


class ConsultaDniPersona(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/dnipersona.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        dni = request.POST.get("dni")
        per, estado = ConsultarDNI(dni, request)
        if estado:
            context["message"] = estado
            context["success"] = False
        else:
            context["success"] = True
            perdata = Persona.objects.filter(pk=per.pk).values(
                "pk", "ubigeo_id", "direccion", "referencia", "correo"
            )
            perresult = list(perdata)[0]
            # Buscamos si ya se ha emitido a esta PERSONA
            periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
            ultimoenvio = Destino.objects.exclude(ultimoestado__estado="AN").filter(
                documento__responsable__area=periodoactual.area,
                personajuridica__isnull=True,
                persona_id=perdata[0]["pk"],
                documento__estadoemitido__isnull=False
            ).order_by("-documento__estadoemitido__creado").first()
            # ).order_by("-documento__creado").first()
            if ultimoenvio:
                perresult["ubigeo_id"] = ultimoenvio.ubigeo.id
                perresult["direccion"] = ultimoenvio.direccion
                perresult["referencia"] = ultimoenvio.referencia
                perresult["correo"] = ultimoenvio.correo
            context["per"] = perresult
        return self.render_to_response(context=context)


class ConsultaDniPersonaOrigen(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/dnipersonaorigen.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        dni = request.POST.get("dni")
        per, estado = ConsultarDNI(dni, request)
        context["success"] = estado is None
        context["message"] = estado
        context["persona"] = per
        return self.render_to_response(context=context)


class ConsultaNoDniPersonaOrigen(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/nodnitramitadororigen.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["success"] = False
        td = TipoDocumentoIdentidad.objects.filter(pk=request.POST.get("td", 0)).first()
        nro = request.POST.get("nro", '').strip()
        if td and len(nro) > 0:
            persona = Persona.objects.filter(tipodocumentoidentidad=td, numero=nro).first()
            if persona:
                context["success"] = True
                context["persona"] = persona
                context["cargo"] = persona.CiudadanoUltimoCargo()
        return self.render_to_response(context=context)


class ConsultaDniTramitadorOrigen(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/dnitramitadororigen.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        dni = request.POST.get("dni")
        per, estado = ConsultarDNI(dni, request)
        context["success"] = estado is None
        context["message"] = estado
        context["persona"] = per
        return self.render_to_response(context=context)
