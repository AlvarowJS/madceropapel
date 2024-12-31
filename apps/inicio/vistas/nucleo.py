"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json

import requests
from django.conf import settings


def ObtenerTokenNucleo():
    urlnucleo = settings.CONFIG_APP["NUCLEO"]["URL"]
    urltoken = "%s/token" % urlnucleo
    r = requests.post(
        urltoken,
        json={
            "User": settings.CONFIG_APP["NUCLEO"]["USUARIO"],
            "Pwd": settings.CONFIG_APP["NUCLEO"]["CLAVE"],
        }
    )
    r.json()
    result = json.loads(r.text)
    token = result["token"]
    return token
