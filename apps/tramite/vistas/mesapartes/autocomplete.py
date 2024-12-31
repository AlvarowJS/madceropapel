"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import F, Case, When
from django.http import JsonResponse
from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import Documento


class AutoCompleteRazonSocial(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        query = self.request.POST.get("query", "")
        cargos = Documento.objects.filter(
            origentipo__in=["F", "V", "X", "C"],
            personajuridicatipo="O"
        ).annotate(
            razoncomercial=Case(
                When(personajuridica__nombrecomercial__isnull=True, then=F("personajuridica__razonsocial")),
                default=F("personajuridica__nombrecomercial")
            )
        ).order_by("razoncomercial")
        if len(query) > 0:
            cargos = cargos.filter(
                razoncomercial__icontains=query
            )
        cargos = cargos.annotate(
            label=F("razoncomercial")
        ).values("label").distinct()
        return JsonResponse(list(cargos), safe=False)


class AutoCompleteCargo(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"
    content_type = "application/json"
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        query = self.request.POST.get("query", "")
        cargos = Documento.objects.filter(
            origentipo__in=["F", "V", "X", "C"]
        ).order_by("ciudadanocargo")
        if len(query) > 0:
            cargos = cargos.filter(
                ciudadanocargo__icontains=query
            )
        cargos = cargos.annotate(
            label=F("ciudadanocargo")
        ).values("label").distinct()
        return JsonResponse(list(cargos), safe=False)
