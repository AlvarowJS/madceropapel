"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

#!/usr/bin/env python
# coding: utf-8
from django.template.loader import get_template
from django.template import Context, Template
from django.utils.safestring import mark_safe


class SearchBox(object):
    def __init__(self, visible=True, placeholder=None, filter_date=False):
        self.visible = visible
        self.placeholder = placeholder or "Buscar"
        self.filter_date = filter_date

    @property
    def dom(self):
        _result = ""
        if self.filter_date:
            _result = "<'col-12 col-sm-6 col-lg-3 mb-2 mb-lg-0'f>"
        elif self.visible:
            _result = "<'col-12 col-lg-4 mb-2 mb-lg-0'f>"

        return _result


class InfoLabel(object):
    def __init__(self, visible=True, format=None):
        self.visible = visible
        self.format = format or "Total _TOTAL_"

    @property
    def dom(self):
        if self.visible:
            return "<'col-6 col-lg-4 d-flex align-items-center'i>"
        else:
            return "<'col-sm-4 col-md-4 col-lg-4'>"


class Pagination(object):
    def __init__(self, visible=True, length=10, first=None,
                 last=None, prev=None, next=None):
        self.visible = visible
        self.length = length
        self.first = first or "<i class='fas fa-angle-double-left'></i>"
        self.last = last or "<i class='fas fa-angle-double-right'></i>"
        self.prev = prev or "<i class='fas fa-angle-left'></i>"
        self.next = next or "<i class='fas fa-angle-right'></i>"

    @property
    def dom(self):
        if self.visible:
            return ("<'col-12 col-lg-4 d-flex justify-content-center justify-content-lg-end'p>")
        else:
            return ("<'col-sm-6 col-md-6 col-lg-6 col-sm-offset-2 "
                    "col-md-offset-2 col-lg-offset-2'>")


class LengthMenu(object):
    def __init__(self, visible=True):
        self.visible = visible

    @property
    def dom(self):
        if self.visible:
            return "<'col-6 col-lg-4 d-flex justify-content-end justify-content-lg-center'l>"
        else:
            return "<'col-sm-4 col-md-4 col-lg-4'>"
