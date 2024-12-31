"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib import admin

# Register your models here.
from apps.tramite.models import DocumentoTipo


class AdminDocumentoTipo(admin.ModelAdmin):
    list_display = ["id", "codigo", "nombre", "nombrecorto"]
    # list_filter = ["codigo", "nombre", "nombrecorto"]
    search_fields = ["codigo", "nombre", "nombrecorto"]
    list_editable = ["codigo", "nombre", "nombrecorto"]
    list_per_page = 10


admin.site.register(DocumentoTipo, AdminDocumentoTipo)
