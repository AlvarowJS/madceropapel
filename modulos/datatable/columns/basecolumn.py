"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.template import Template, Context
from django.urls import reverse
from django.utils.html import escape
from pytz import timezone

from modulos.datatable.columns import Column
from django.utils.translation import gettext_lazy as _

from modulos.datatable.utils import Accessor


class Columna(Column):
    def __init__(self, position=None, tachar=None, displaytext=None, *args, **kwargs):
        super(Columna, self).__init__(*args, **kwargs)
        hattrs = self.header.base_attrs
        self.header.base_attrs = hattrs
        cattrs = self.attrs
        if position:
            positionT = "text-" + position
            if cattrs.keys().__contains__("class"):
                if not cattrs["class"].__contains__(positionT):
                    cattrs["class"] += " " + positionT
            else:
                cattrs["class"] = positionT
        self.attrs = cattrs
        self.tachar = tachar
        self.displaytext = displaytext

    def render(self, obj):
        _result = super(Columna, self).render(obj)
        if self.displaytext:
            _result = Accessor(self.displaytext).resolve(obj)
            _result = "" if _result is None else escape(_result)
        else:
            if self.tachar:
                if not eval("obj." + self.tachar):
                    _result = "<del>%s</del>" % _result
        return _result


class ColumnaBoolean(Columna):
    def __init__(self, choices=None, *args, **kwargs):
        super(ColumnaBoolean, self).__init__(*args, **kwargs)
        self.choices = choices

    def render(self, obj):
        _result = ""
        _valor = Accessor(self.field).resolve(obj)
        if not _valor is None:
            for choice in self.choices:
                if choice[0] == _valor:
                    _result = choice[1]
                    break
        return escape(_result)


class ColumnaAcciones(Columna):
    def __init__(self, url_edit=None, url_delete=None, url_otras=None, ventana_tamanio="md",
                 ventana_modal="#modal-principal-centro", visible=True, pk="pk"):
        self.url_edit = url_edit
        self.url_delete = url_delete
        self.url_otras = url_otras
        self.ventana_modal = ventana_modal
        self.ventana_tamanio = ventana_tamanio
        self.pk = pk
        _canacc = 0
        if url_edit:
            _canacc += 1
        if url_delete:
            _canacc += 1
        _canacc += len(url_otras or [])
        _canacc = "%spx" % (25 * _canacc + 20)
        super(ColumnaAcciones, self).__init__(
            field="pk",
            header="Acciones",
            header_attrs={"class": "text-center nowrap", "style": "width: " + _canacc},
            attrs={"class": "text-center"},
            sortable=False,
            searchable=False,
            visible=visible,
            position="center"
        )

    def render(self, obj):
        _result = ""
        if isinstance(obj, dict):
            valpk = obj[self.pk]
        else:
            valpk = eval("obj." + self.pk)
        if self.url_edit and obj.canedit:
            urledit = reverse(self.url_edit, kwargs={"pk": valpk})
            _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='%s' " + \
                       "data-target='%s' title='%s' rel='tooltip' " + \
                       "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                       "<span class='flaticon-edit'></span></a>"
            _result = _result % (urledit, self.ventana_tamanio, self.ventana_modal, "Editar")
        if self.url_delete and obj.candelete:
            urldelete = reverse(self.url_delete, kwargs={"pk": valpk})
            _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='%s' " + \
                       "data-target='%s' title='%s' rel='tooltip' " + \
                       "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                       "<span class='flaticon-delete'></span></a>"
            _result = _result % (urldelete, self.ventana_tamanio, self.ventana_modal, "Eliminar")
        if self.url_otras:
            for otra in self.url_otras:
                if otra.get("kwargs"):
                    kw = otra.get("kwargs")
                    kwargs = dict()
                    for key in kw:
                        if isinstance(obj, dict):
                            kwargs[key] = obj[kw[key]]
                        else:
                            kwargs[key] = eval("obj." + kw[key])
                else:
                    kwargs = {"pk": obj.pk}
                urlotra = reverse(otra["url"], kwargs=kwargs)
                _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='%s' " + \
                           "data-target='%s' title='%s' rel='tooltip' " + \
                           "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                           "<span class='%s'></i></span>"
                _result = _result % (urlotra, self.ventana_tamanio, self.ventana_modal, otra["title"], otra["icono"])
        # if len(_result) > 0:
        #     _result = "<ul class='table-controls'>" + _result + "</ul>"
        return _result


class ColumnaNumero(Columna):
    def __init__(self, decimales=2, *args, **kwargs):
        super(ColumnaNumero, self).__init__(position="right", *args, **kwargs)
        self.decimales = decimales

    def render(self, obj):
        _result = Accessor(self.field).resolve(obj)
        if _result:
            formato = "{0:.%sf}" % self.decimales
            _result = formato.format(_result)
        return _result or ""


class ColumnaIcono(Columna):
    def __init__(self, size=None, *args, **kwargs):
        super(ColumnaIcono, self).__init__(position="center", *args, **kwargs)
        self.size = size

    def render(self, obj):
        _result = Accessor(self.field).resolve(obj)
        if _result:
            size = self.size
            if size:
                size = " fa-%sx" % size
            else:
                size = ""
            _result = "<i class='%s%s'></i>" % (_result, size)
        return _result or ""


class ColumnaColor(Columna):
    def __init__(self, *args, **kwargs):
        super(ColumnaColor, self).__init__(position="center", *args, **kwargs)

    def render(self, obj):
        _result = Accessor(self.field).resolve(obj)
        if _result:
            _result = "<span class='badge badge-pills rounded-circle px-2 border' " + \
                      "style='background-color: %s;'>&nbsp;&nbsp;</span>" % _result
        return _result or ""


class ColumnaImagen(Columna):
    def __init__(self, width=None, height=None, title="", thumb=None, *args, **kwargs):
        super(ColumnaImagen, self).__init__(position="center", *args, **kwargs)
        self.width = width
        self.height = height
        self.title = title
        self.thumb = thumb

    def render(self, obj):
        path = Accessor(self.field).resolve(obj)
        pathmini = None
        if self.thumb:
            pathmini = Accessor(self.thumb).resolve(obj)
        _result = ""
        if not pathmini:
            pathmini = path
        if path:
            width = ""
            height = ""
            if self.width:
                width = " width='%s'" % self.width
            if self.height:
                height = " height='%s'" % self.height
            actualizado = Accessor("actualizado").resolve(obj).strftime("%Y%m%d%H%M%S")
            path = path.url
            path = "%s?%s" % (path, actualizado)
            pathmini = pathmini.url
            pathmini = "%s?%s" % (pathmini, actualizado)
            tpl = '<img src="%s"%s%s>' % (pathmini, width, height)
            tplzoom = '<a class="image-popup-vertical-fit" href="%s" title="%s">%s</a>' % (
                path, self.title, tpl
            )
            _result = Template(tplzoom).render(Context())
        return _result


class ColumnaVideo(Columna):
    def __init__(self, field_image, width=None, height=None, *args, **kwargs):
        super(ColumnaVideo, self).__init__(position="center", *args, **kwargs)
        self.width = width
        self.height = height
        self.field_image = field_image

    def render(self, obj):
        _result = ""
        pathImg = Accessor(self.field_image).resolve(obj)
        if pathImg:
            width = ""
            height = ""
            if self.width:
                width = " width='%s'" % self.width
            if self.height:
                height = " height='%s'" % self.height
            imagen = pathImg.url
            actualizado = Accessor("actualizado").resolve(obj)
            if actualizado:
                imagen = "%s?%s" % (imagen, actualizado.strftime("%Y%m%d%H%M%S"))
            tpl = '<div class="modal-video">'
            tpl += '<div class="modal-video-container text-center">'
            tpl += '<img class="img-fluid" src="%s" alt="" data-toggle="modal" data-target="#modalVideo"'
            tpl += '%s%s>'
            tpl += '<i id="link" data-codigo="%s" class="flaticon-youtube-play-button-line"></i>'
            tpl += '</div>'
            tpl += '</div>'
            tpl = tpl % (imagen, width, height, Accessor(self.field).resolve(obj))
            _result = Template(tpl).render(Context())
        return _result


class ColumnaFecha(Columna):
    # Formato Fecha/Hora = "%d/%m/%Y %I:%M %p"
    def __init__(self, field=None, header=None, attrs=None, header_attrs=None, format="%d/%m/%Y", sortable=True):
        super(ColumnaFecha, self).__init__(
            field=field, header=header, header_attrs=header_attrs, attrs=attrs, searchable=False, sortable=sortable,
            position="center"
        )
        self.format = format

    def render(self, obj):
        # print(type(obj), obj.pk)
        valor = eval("obj." + self.field)
        _result = ""
        if valor:
            if hasattr(valor, "astimezone"):
                valor = valor.astimezone(timezone(settings.TIME_ZONE))
            _result = valor.strftime(self.format)
        return _result


class ColumnCheckSelect(Columna):
    def render(self, obj):
        return '<label class="checkbox checkbox-single checkbox-primary mb-0">' + \
               '<input type="checkbox" value="" class="checkable"/>' + \
               '<span></span>' + \
               '</label>'
