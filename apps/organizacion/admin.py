"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib import admin

# Register your models here.
from apps.organizacion.models import *


class AdminDependencia(admin.ModelAdmin):
    list_display = ["id", "orden", "codigo", "nombre", "siglas"]
    list_filter = ["codigo", "nombre", "siglas"]
    search_fields = ["codigo", "nombre", "siglas"]
    list_editable = ["codigo", "nombre", "siglas"]
    list_per_page = 10


class AdminAreaTipo(admin.ModelAdmin):
    list_display = ["id", "codigo", "nombre"]
    list_filter = ["codigo", "nombre"]
    search_fields = ["codigo", "nombre"]
    list_editable = ["codigo", "nombre"]
    list_per_page = 10


class AdminArea(admin.ModelAdmin):
    list_display = ["id", "orden", "nombre", "siglas", "areatipo"]
    list_filter = ["nombre", "siglas", "areatipo"]
    search_fields = ["nombre", "siglas"]
    list_editable = ["nombre", "siglas"]
    list_per_page = 10


admin.site.register(Dependencia, AdminDependencia)
admin.site.register(AreaTipo, AdminAreaTipo)
admin.site.register(Area, AdminArea)
