"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import authenticate
from django.template.loader import render_to_string
from ldap3 import Server, Connection
from django.utils.translation import gettext_lazy as _

from apps.inicio.models import PersonaTablero, Tablero
from apps.inicio.vistas.dashboard import MAX_REG_DASH
from apps.tramite.vistas.bandejas import *


@database_sync_to_async
def set_tablero(user, data):
    for tabord in data:
        tablero = PersonaTablero.objects.filter(id=tabord["id"]).first()
        if tablero:
            tablero.orden = tabord["orden"]
            tablero.save()


@database_sync_to_async
def set_tablero_expandido(data):
    pt = PersonaTablero.objects.filter(pk=data["id"]).first()
    if pt:
        pt.expandido = data["expandido"]
        pt.save()


@database_sync_to_async
def set_menu_estado(user, estado):
    pc = user.persona.personaconfiguracion
    pc.menuabierto = estado
    pc.save()


def get_contador_bandeja(request, key, modo, menu):
    data = {}
    try:
        cantidad = 0
        if menu.codigo == "dbEnProyecto":
            cantidad = eval("Query%sBandeja%s(request).filter(ultimoestado__estado='PY').count()" % (
                modo,
                menu.codigo.replace("db", "")
            ))
        elif menu.codigo == "dbFirmaVB":
            cantidad = eval("Query%sBandeja%s(request).filter(estado__codigo='SF').count()" % (
                modo,
                menu.codigo.replace("db", "")
            ))
        elif not menu.codigo in ["dbRecepcionados", "dbMiMensajeria"]:
            cantidad = eval("Query%sBandeja%s(request).count()" % (
                modo,
                menu.codigo.replace("db", "")
            ))
        if menu.codigo == "dbRecepcionados":
            cantidad = eval("Query%sBandeja%s(request).filter(ultimoestado__estado='RE').count()" % (
                modo,
                menu.codigo.replace("db", "")
            ))
        elif menu.codigo == "dbMiMensajeria":
            cantidad = eval("Query%sBandeja%s(request).filter(ultimoestadomensajeria__estado__in=['DA','DM']).count()" % (
                modo,
                menu.codigo.replace("db", "")
            ))
        elif menu.codigo == "dbFirmaVB":
            cantidad += eval("Query%sAnexo%s(request).filter(estado='SF').count()" % (
                modo,
                menu.codigo.replace("db", "")
            ))
        obj = menu.codigo + key
        if menu.codigo == "dbMiMensajeria" and key == "O":
            obj = menu.codigo + "M"
        data[obj] = {
            "cantidad": cantidad
        }
    except Exception as e:
        # print(e)
        pass
    return data


@database_sync_to_async
def get_contadores(request):
    data = {}
    modos = {"O": "Oficina", "P": "Personal"}
    for key, modo in modos.items():
        for menu in Tablero.objects.order_by("orden"):
            data.update(get_contador_bandeja(request, key, modo, menu))
    return data


@database_sync_to_async
def get_contador(request, _datos):
    data = {}
    modos = {"O": "Oficina", "P": "Personal"}
    for key in _datos["keys"].split(","):
        for menu in _datos["menus"].split(","):
            tablero = Tablero.objects.filter(codigo=menu).first()
            data.update(get_contador_bandeja(request, key, modos[key], tablero))
    return data


@database_sync_to_async
def set_sesion_bloqueada(user):
    if hasattr(user, "persona"):
        pc = user.persona.personaconfiguracion
        pc.bloqueado = True
        pc.save()


@database_sync_to_async
def set_sesion_desbloquear(user, pw):
    _result = False
    _message = ""
    # Verificamos la contraseña en Dominio
    if hasattr(user, "persona") and settings.CONFIG_APP["LDAP"]["STATUS"]:
        domain = "ldap://" + '.'.join([
            settings.CONFIG_APP["LDAP"]["DOMAIN"],
            settings.CONFIG_APP["LDAP"]["DC1"],
            settings.CONFIG_APP["LDAP"]["DC2"]
        ])
        oServer = Server(
            domain,
            use_ssl=settings.CONFIG_APP["LDAP"]["SSL"],
            port=settings.CONFIG_APP["LDAP"]["PORT"]
        )
        oUser = "%s\%s" % (
            settings.CONFIG_APP["LDAP"]["DOMAIN"],
            user.persona.personaconfiguracion.usuariodominio
        )
        try:
            Connection(oServer, user=oUser, password=pw, read_only=True, auto_bind=True)
            _result = True
        except Exception as e:
            _message = str(e)
            # _message = "La contraseña es incorrecta"
    # Si no es correcta la contraseña de Dominio verificamos en Django
    if not _result:
        try:
            userlogin = authenticate(username=user.username, password=pw)
            if userlogin is None:
                _message = str(_(
                    "Your old password was entered incorrectly. Please enter it again."
                )).replace("antigua ", "")
            else:
                _result = True
        except Exception as e:
            _message = str(e)
            # _message = "La contraseña es incorrecta"
    if _result:
        _message = ""
        if hasattr(user, "persona"):
            pc = user.persona.personaconfiguracion
            pc.bloqueado = False
            pc.save()
    return _result, _message


@database_sync_to_async
def get_tablerodata(request, tablero):
    tablerox = tablero.replace("db", "")
    if not hasattr(request, "META"):
        setattr(request, "META", {"REMOTE_ADDR": ""})
    data = eval("QueryTablero" + tablerox + "(request)")
    if tablerox == "EnProyecto":
        data = data.filter(
            ultimoestado__estado="PY"
        )
    elif tablerox == "FirmaVB":
        data = data.filter(
            estado__codigo="SF"
        )
    result = {
        "codigo": tablero,
        "data": json.loads(
            render_to_string(
                "inicio/dashboard/lista.html",
                context={
                    "total": data.count(),
                    "maximo": MAX_REG_DASH,
                    "data": data[:MAX_REG_DASH],
                    "tabobj": Tablero.objects.get(codigo=tablero)
                },
                request=request
            )
        )
    }
    return result


@database_sync_to_async
def get_notificaciones(request):
    result = [
        {
            "expediente": "9500",
            "documento": "El documento N°",
            "observacion": "Dato"
        }
    ]
    return result
