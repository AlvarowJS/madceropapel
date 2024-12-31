"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib import admin

# Register your models here.
from apps.inicio.models import *


class AdminTipoDocumentoIdentidad(admin.ModelAdmin):
    list_display = ["id", "codigo", "nombre", "abreviatura"]
    list_filter = ["codigo", "nombre", "abreviatura"]
    search_fields = ["codigo", "nombre", "abreviatura"]
    list_editable = ["codigo", "nombre", "abreviatura"]


class AdminPersona(admin.ModelAdmin):
    list_display = ["id", "tipodocumentoidentidad", "numero", "apellidocompleto", "ultimoperiodotrabajo"]
    list_filter = ["numero", "apellidocompleto"]
    search_fields = ["numero", "apellidocompleto"]
    # list_editable = ["numero", "apellidocompleto"]
    list_per_page = 10


class AdminPersonaJuridica(admin.ModelAdmin):
    list_display = ["id", "tipo", "ruc", "razonsocial", "nombrecomercial"]
    # list_filter = ["ruc", "razonsocial", "nombrecomercial"]
    search_fields = ["ruc", "razonsocial", "nombrecomercial"]
    # list_editable = ["numero", "apellidocompleto"]
    list_per_page = 10


admin.site.register(TipoDocumentoIdentidad, AdminTipoDocumentoIdentidad)
admin.site.register(Persona, AdminPersona)
admin.site.register(PersonaJuridica, AdminPersonaJuridica)
