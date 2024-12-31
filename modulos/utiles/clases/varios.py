"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import io
import random
import string
from datetime import date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from pytz import timezone as pytz_timezone

from babel.dates import format_date
from dateutil import relativedelta
from django.utils import timezone


def randomString(cantidad=5, mayusculas=True, modo="NL"):
    # modo: N solo números, L solo letras, NL números y letras
    letters = string.ascii_uppercase if mayusculas else string.ascii_lowercase
    numbers = string.digits
    lista = letters
    if modo == "N":
        lista = numbers
    elif modo == "NL":
        lista = letters + numbers
    return ''.join(random.choice(lista) for i in range(cantidad))


def obtenerEdad(fecNacimiento, opciones=''):
    opciones = opciones.split(",")

    resta = relativedelta.relativedelta(date.today(), fecNacimiento)

    anios = resta.years
    meses = resta.months
    dias = resta.days

    textoEdad = str(anios)

    if 'a' in opciones or 'A' in opciones:
        textoEdad += ' años '
    if 'm' in opciones or 'M' in opciones:
        textoEdad += str(meses) + ' meses '
    if 'd' in opciones or 'D' in opciones:
        textoEdad += str(dias) + ' días '

    return textoEdad


def getMac():
    from uuid import getnode as get_mac
    mac = get_mac()
    mac = ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
    return mac


def ofuscarCorreo(correo):
    pedazos = correo.split("@")
    pedazos[0] = pedazos[0][:3] + "*" * 3
    return "@".join(pedazos)


def maximo(lista):
    return max(i for i in lista if i is not None)


def minimo(lista):
    return min(i for i in lista if i is not None)


class Dict2Obj(object):
    def __init__(self, dictionary):
        """Constructor"""
        for key in dictionary:
            setattr(self, key, dictionary[key])


def Titular(nombre):
    if nombre:
        palabras_fijas = ["de", "del", "las", "la", "los"]
        palabras = str(nombre).split(" ")
        for idx, palabra in enumerate(palabras):
            if palabra.lower() in palabras_fijas:
                palabras[idx] = palabra.lower()
            else:
                palabras[idx] = palabra.title()
        nombre = " ".join(palabras)
    return nombre


def replace_characters(cadena):
    cadena_nueva = ""
    caracteres = [
        {"numold": 8220, "numnew": 34},
        {"numold": 8221, "numnew": 34},
    ]
    for letra in cadena:
        reemplazo = next((item for item in caracteres if ord(letra) == item["numold"]), None)
        if reemplazo:
            cadena_nueva += chr(reemplazo["numnew"])
        else:
            cadena_nueva += letra
    return cadena_nueva


def RemoverCaracteresEspeciales(texto):
    _nombre = ""
    for car in texto:
        if not ord(car) in [61692, 9]:
            _nombre += car
    return _nombre


def formatdate(fecha):
    _result = str(format_date(
        fecha, format="dd 'de' MMMM 'de' yyyy", locale="es"
    ))
    _result = ''.join(c.upper() if i == 6 else c for i, c in enumerate(_result))
    return _result


def load_bytes(ruta):
    _filebin = open(ruta, "rb")
    _filedata = io.BytesIO()
    _filedata.write(_filebin.read())
    _filebin.close()
    _filedata.seek(0)
    return _filedata


def ConvertPica(cantidad):
    # return round(cantidad * 1.0036801605888256942121110739378, 2)
    return cantidad * 1.0036801605888256942121110739378


def DiasHabiles(fecha, dias, sentido):
    fecha = fecha or timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
    _contador = 0
    _totales = 0
    while True:
        if (fecha + sentido * timezone.timedelta(days=_contador)).strftime("%A").lower() not in ["sunday", "saturday"]:
            _totales += 1
        _contador += 1
        if _totales == dias:
            break
    return _contador - 1


@deconstructible
class FileDimensionValidator:
    message = "El tamaño debe ser %(width)d de ancho por %(height)d de alto en pixeles."
    code = "invalid_dimensions"

    def __init__(self, width=None, height=None, message=None, code=None):
        self.width = width
        self.height = height
        self.message = message or self.message
        self.code = code or self.code

    def __call__(self, image):
        error = False
        if self.width is not None and image.width != self.width:
            error = True
        if self.height is not None and image.height != self.height:
            error = True
        if error:
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "width": self.width,
                    "height": self.height,
                    "value": image
                }
            )

    def __eq__(self, other):
        return (
                isinstance(other, self.__class__)
                and self.width == other.width
                and self.height == other.height
                and self.message == other.message
                and self.code == other.code
        )
