"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

#!/usr/bin/env python
# coding: utf-8
from django.conf.urls import url

from modulos.datatable.views import FeedDataView


urlpatterns = [
    url(r'^ajax/(?P<token>\w{32})/$', FeedDataView.as_view(), name='feed_data'),
]
