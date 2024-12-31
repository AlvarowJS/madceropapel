"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from urllib.parse import quote

from django.http import HttpResponse
from django.template import loader


def error400(request, exception=None):
    template = loader.get_template('error/400.html')
    context = {
        'request_path': quote(request.path),
        'message': 'All: %s' % request
    }
    return HttpResponse(content=template.render(context, request), content_type='text/html; charset=utf-8', status=404)


def error403(request, exception=None):
    template = loader.get_template('error/403.html')
    context = {
        'message': 'All: %s' % request
    }
    return HttpResponse(content=template.render(context, request), content_type='text/html; charset=utf-8', status=403)


def error404(request, exception=None):
    template = loader.get_template('error/404.html')
    exception_repr = exception.__class__.__name__
    try:
        message = exception.args[0]
    except (AttributeError, IndexError):
        pass
    else:
        if isinstance(message, str):
            exception_repr = message
    context = {
        'request_path': quote(request.path),
        'exception': exception_repr,
    }
    return HttpResponse(content=template.render(context, request), content_type='text/html; charset=utf-8', status=404)


def error500(request, exception=None):
    template = loader.get_template('error/500.html')
    context = {
        'message': 'All: %s' % request
    }
    return HttpResponse(content=template.render(context, request), content_type='text/html; charset=utf-8', status=500)
