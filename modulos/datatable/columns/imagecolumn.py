"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

#!/usr/bin/env python
# coding: utf-8
from django.template import Template, Context

from modulos.datatable.columns.basecolumn import Columna
from modulos.datatable.utils import Accessor


class ImageColumn(Columna):
    def __init__(self, field=None, field_title=None, width='auto', zoom=True, *args, **kwargs):
        kwargs["sortable"] = False
        kwargs["searchable"] = False
        self.field_title = field_title
        self.width = width
        self.zoom = zoom
        super(ImageColumn, self).__init__(field=field, position="center", *args, **kwargs)

    def render(self, obj):
        path = Accessor(self.field).resolve(obj)
        title = ""
        if self.field_title:
            title = Accessor(self.field_title).resolve(obj)
            if not title:
                title = ""
        _result = ""
        if path:
            tpl = '<img src="%s" title="%s" width="%s">' % (path.url, title, self.width)
            if self.zoom:
                tplzoom = '<a class="image-popup-vertical-fit" href="%s" title="%s">%s</a>'
                tpl = tplzoom % (path.url, title, tpl)
            template = Template(tpl)
            return template.render(Context())
        return _result
