"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import datetime
import json
import ntpath
import os
import random
import uuid
from base64 import b64encode

import magic
from babel.dates import format_date, format_datetime
from django import template
from django.conf import settings
from django.forms.models import ModelChoiceIteratorValue
from django.template.defaulttags import URLNode
from django.urls import reverse, get_resolver
from django.utils.safestring import mark_safe
from django.utils.timezone import make_aware

from modulos.utiles.templatetags.lenguaje import idioma

register = template.Library()


@register.simple_tag(takes_context=True)
def setvarparentblock(context, key, value):
    context.dicts[-2][key] = value
    return ''


@register.simple_tag(takes_context=True)
def setvar(context, key, value):
    context[key] = value
    return ''


@register.filter
def dividir(dividendo, divisor):
    return int(dividendo / divisor)


@register.filter
def multiplicar(valor1, valor2):
    return valor1 * valor2


@register.filter
def filename(campo, frominitial=False):
    valor = None
    if frominitial:
        valor = campo.initial
    elif campo.value():
        valor = campo.value()
    if valor and hasattr(valor, "path"):
        return ntpath.basename(valor.path)
    else:
        return ""


@register.filter
def fileexist(filename):
    _result = False
    if filename:
        if hasattr(filename, "path"):
            _result = os.path.exists(filename.path)
    return _result


@register.filter
def getattr(attrs, attr):
    return attrs.get(attr, None)


@register.filter(name='formatearnumero')
def formatearnumero(value, decimales):
    if value:
        formato = "{0:.%sf}" % decimales
        return formato.format(value)
    else:
        return None


@register.simple_tag(takes_context=True)
def get_config(context, qs, codigo):
    _result = ""
    registro = qs.filter(codigo=codigo).first()
    if registro:
        _result = idioma(context, registro, "valor")
    return _result


@register.filter
def restar(arg1, arg2):
    return int(arg1) - int(arg2)


@register.filter
def get_attr(obj, attr):
    return obj.get(attr)


@register.filter
def zfill(numero, cantidad):
    return str(numero).zfill(cantidad)


@register.filter
def rango(inicio, fin):
    return range(inicio, fin + 1)


@register.filter
def concatenar(cadenabase, cadenaadicional):
    return "%s%s" % (cadenabase, cadenaadicional)


@register.filter
def separar(cadena, separador):
    return str(cadena).split(separador)


@register.filter
def elemento(lista, indice):
    return lista[indice]


@register.filter
def bin_2_img(_bin):
    if _bin is not None: return b64encode(_bin).decode('utf-8')


@register.filter
def tipo(objeto):
    _tipo = type(objeto)
    if hasattr(_tipo, "__name__"):
        _tipo = str(_tipo.__name__).lower()
    return _tipo


@register.filter
def entero(valor):
    return int(valor or "0")


@register.filter
def iguala(valor1, valor2):
    if isinstance(valor2, ModelChoiceIteratorValue):
        valor2 = valor2.value
    return valor1 == valor2


@register.filter
def formatdate(valor, formato):
    return format_date(valor, format=formato, locale="es")


@register.filter
def formatdatetime(valor, formato):
    return format_datetime(valor, format=formato, locale="es")


@register.filter
def urlresolve(viewname, parametros):
    path, view = viewname.split(':')
    resolver = get_resolver(None)
    extra, resolver = resolver.namespace_dict[path]
    args = []
    kwargs = {}
    parametros = parametros.split("//")
    for patron in resolver.url_patterns:
        if hasattr(patron, "name") and patron.name == view:
            cont = 0
            for key, value in patron.__dict__["pattern"].converters.items():
                kwargs[key] = parametros[cont]
                cont += 1
    return reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def mimetype(datafile):
    return magic.from_buffer(datafile, mime=True)


@register.filter
def get_extension(nombre):
    return os.path.splitext(nombre)[1][1:].lower()


@register.filter
def espdf(datafile):
    return magic.from_buffer(datafile, mime=True) == "application/pdf"


@register.filter
def evaluar(valor):
    return None if not valor else eval(valor)


@register.simple_tag(takes_context=True)
def seturl(context, variable, viewname, *args):
    path, view = viewname.split(':')
    resolver = get_resolver(None)
    extra, resolver = resolver.namespace_dict[path]
    kwargs = {}
    for patron in resolver.url_patterns:
        if hasattr(patron, "name") and patron.name == view:
            cont = 0
            for key, value in patron.__dict__["pattern"].converters.items():
                if cont < len(args):
                    kwargs[key] = args[cont]
                    cont += 1
    context[variable] = reverse(viewname, args=[], kwargs=kwargs)
    return ''


@register.filter
def saltolinea(valor, separador):
    return None if not valor else separador.join(valor.splitlines())


@register.filter
def tiemposegundos(valor):
    return None if not valor else int(valor.timestamp())


@register.filter
def diasrestantes(valor):
    return None if not valor else (valor - make_aware(datetime.datetime.now())).days


@register.simple_tag(takes_context=True)
def aleatorio(context, inicio=None, fin=None, *args):
    inicio = inicio or 0
    fin = fin or 100000
    return random.randint(inicio, fin)


@register.simple_tag(takes_context=True)
def img2b64(context, imagen, img_alto=None, *args):
    _result = "data:image/png;base64,%s" % base64.b64encode(imagen).decode("utf-8")
    if img_alto:
        _result = "<img src='%s' alt='' title='' height='%s'>" % (_result, img_alto)
    return mark_safe(_result)


@register.filter
def equalto(valor1, valor2):
    return valor1 == valor2


@register.filter
def repetir(valor, cantidad):
    return valor * cantidad


@register.filter
def json_loads(valor):
    return json.loads(valor)


@register.filter
def charespecials(valor):
    from modulos.utiles.clases.varios import RemoverCaracteresEspeciales
    return RemoverCaracteresEspeciales(valor)


@register.simple_tag(name='cache_bust')
def cache_bust():
    version = settings.CONFIG_APP.get("VersionProyecto", uuid.uuid4().hex)
    return '__v__={version}'.format(version=version)


@register.filter
def estaen(valor, lista):
    return str(valor) in lista.split(",")


@register.filter
def encampo(valor, campo):
    return str(valor) in campo.__str__()


@register.filter
def absoluto(cantidad):
    return abs(cantidad)


@register.filter
def string(valor):
    return str(valor)
