"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def idioma(context, modelo, campo):
    lc = context["LANGUAGE_CODE"]
    lc = "" if lc == "en" else ("_" + lc)
    _result = ""
    try:
        _result = eval("%s.%s%s" % ("modelo", campo, lc))
    except:
        pass
    return mark_safe(_result or '')


