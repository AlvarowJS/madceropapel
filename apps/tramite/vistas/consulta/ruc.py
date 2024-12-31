"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.models import PersonaJuridica
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import Destino
from apps.tramite.vistas.varios import ConsultarRUC
from modulos.utiles.clases.ruc import ClaseRUC


class ConsultaRucDestino(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/rucdestino.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        ruc = request.POST.get("ruc")
        cr = ClaseRUC('')
        context["success"] = False
        if cr.ValidarRUC(ruc):
            pj, estado = ConsultarRUC(ruc, request)
            if estado:
                context["message"] = estado
            elif pj:
                context["success"] = True
                pjdata = PersonaJuridica.objects.filter(pk=pj.pk).values(
                    "pk", "ubigeo_id", "direccion", "correo", "telefono",
                    "representante__numero", "representantecargo"
                )
                pjresult = list(pjdata)[0]
                # Buscamos si ya se ha emitido a esta PJ
                periodoactual = request.user.persona.periodotrabajoactual(request.session.get("cambioperiodo"))
                ultimoenvio = Destino.objects.exclude(ultimoestado__estado="AN").filter(
                    documento__emisor__area=periodoactual.area,
                    personajuridica_id=pjdata[0]["pk"],
                    documento__estadoemitido__isnull=False
                ).order_by("-documento__estadoemitido__creado").first()
                # print(ultimoenvio.documento.expediente.numero)
                # ).order_by("-documento__creado").first()
                if ultimoenvio:
                    pjresult["ubigeo_id"] = ultimoenvio.ubigeo.id
                    pjresult["direccion"] = ultimoenvio.direccion
                    if ultimoenvio.persona:
                        pjresult["representante__numero"] = ultimoenvio.persona.numero
                        pjresult["representantecargo"] = ultimoenvio.personacargo
                context["pj"] = pjresult
        else:
            context["message"] = "El RUC no es válido"
        return self.render_to_response(context=context)


class ConsultaRucOrigen(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/rucorigen.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        ruc = request.POST.get("ruc")
        cr = ClaseRUC('')
        pj = None
        success = True
        if cr.ValidarRUC(ruc):
            pj, estado = ConsultarRUC(ruc, request)
            if estado:
                success = False
                context["message"] = estado
        else:
            success = False
            context["message"] = "RUC no válido"
        context["success"] = success
        context["pj"] = pj
        return self.render_to_response(context=context)


class ConsultaRazonSocial(TemplateValidaLogin, TemplateView):
    template_name = "tramite/consulta/razonsocial.html"
