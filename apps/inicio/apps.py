"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.apps import AppConfig


class InicioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inicio'