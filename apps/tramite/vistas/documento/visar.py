"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.views.generic import TemplateView

from apps.inicio.vistas.inicio import TemplateValidaLogin


class DocumentoVisar(TemplateValidaLogin, TemplateView):
    template_name = "tramite/documento/visar.html"
