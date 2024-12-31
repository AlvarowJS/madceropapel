"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

#!/usr/bin/env python
# coding: utf-8
from datetime import datetime

from django.conf import settings
from django.utils.html import escape

from modulos.datatable.utils import Accessor
from .base import Column
from .basecolumn import Columna
from pytz import timezone as pytz_timezone


class DatetimeColumn(Columna):
    DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, format=None, **kwargs):
        self.format = format or DatetimeColumn.DEFAULT_FORMAT
        super(DatetimeColumn, self).__init__(position="center", **kwargs)

    def render(self, obj):
        tiempo = Accessor(self.field).resolve(obj)
        if tiempo:
            if isinstance(tiempo, datetime):
                tiempo = tiempo.astimezone(pytz_timezone(settings.TIME_ZONE))
            text = tiempo.strftime(self.format).lower()
        else:
            text = ""
        return escape(text)
