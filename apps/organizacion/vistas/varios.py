"""
    @autor Dirección Regional de Transformación Digital
    @titularidad GOBIERNO REGIONAL CAJAMARCA
    @licencia Python Software Foundation License. Ver LICENCIA.txt
    @año 2022
"""
from django.conf import settings

from apps.organizacion.models import Dependencia


def listalogos():
    result = dict()
    dep = Dependencia.objects.filter(codigo=settings.CONFIG_APP["Dependencia"]).first()
    if dep and not dep.sello_firmagrc:
        result = {
            "firma": dep.sello_firma.url or "",
            "sello_cargo": dep.sello_cargo.url or "",
            "sello_vb": dep.sello_vistobueno.url or "",
            "sello_firma_ad": dep.sello_firma_adicional.url or ""
        }
    return result
