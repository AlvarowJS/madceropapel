"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django import template
from django.db.models import Q, Value

register = template.Library()


def get_context(max_depth=4):
    import inspect
    stack = inspect.stack()[2:max_depth]
    context = {}
    for frame_info in stack:
        frame = frame_info[0]
        arg_info = inspect.getargvalues(frame)
        if 'context' in arg_info.locals:
            context = arg_info.locals['context']
            break
    return context


def split(texto, separator):
    return texto.split(separator)


@register.filter(name='querysort')
def querysort(query, ordenes):
    ordenes = split(ordenes, ",")
    makesort = "query.order_by("
    for orden in ordenes:
        makesort += "'" + orden + "',"
    makesort = makesort[:-1] + ")"
    return eval(makesort)


@register.filter(name='queryexclude')
def queryexclude(query, exclusion):
    return eval("query.exclude(" + exclusion + ")")


@register.filter(name='queryfilter')
def queryfilter(query, filtro):
    return eval("query.filter(" + filtro + ")")


@register.filter(name='querycount')
def querycount(query):
    return query.count()


@register.filter(name='queryfirst')
def queryfirst(query, field=None):
    _data = query.first()
    if field:
        _data = eval("_data." + field)
    return _data


@register.filter(name='queryfirmador')
def queryfirmador(query, user):
    # encargos = user.persona.TrabajosActivos().filter(tipo__in=["EN", "EP"]).values_list("area_id")
    __request = get_context().get("request")
    periodoactual = __request.user.persona.periodotrabajoactual(__request.session.get("cambioperiodo"))
    if periodoactual.tipo == "EN":
        return query.filter(
            empleado__area=periodoactual.area
        ).first()
    else:
        return query.filter(
            empleado=periodoactual
        ).first()


@register.filter(name='querygetvalue')
def querygetvalue(query, campo):
    return eval("query." + campo)


@register.filter(name='periodoactual')
def periodoactual(campo, continuo=None):
    _result = ""
    __request = get_context().get("request")
    if __request:
        if not __request.user.is_superuser:
            _result = campo.periodotrabajoactual(__request.session.get("cambioperiodo"))
    if continuo and not __request.user.is_superuser:
        _result = eval("_result." + continuo)
    return _result


@register.filter(name='len_in_mb')
def len_in_mb(tamanio):
    return "%s MB" % round(tamanio / 1024 / 1024, 2)


@register.filter(name='querydocdessize')
def querydocdessize(id):
    from apps.tramite.models import Destino
    des = Destino.objects.filter(pk=id).first()
    _size = 0
    if des.documento.documentotipoarea.documentotipo.esmultiple and \
            not des.documento.documentotipoarea.documentotipo.esmultipledestino and \
            des.documento.forma == "I":
        docpdf = des.documento.documentoplantilla.documentopdf_set.first()
        if docpdf:
            docpdf = docpdf.pdffirma or docpdf.pdf
    else:
        docpdf = des.documento.documentoplantilla.documentopdf_set.first()
        if docpdf:
            docpdf = docpdf.pdffirma or docpdf.pdf
    if docpdf:
        _size = len(docpdf)
    return len_in_mb(_size)
