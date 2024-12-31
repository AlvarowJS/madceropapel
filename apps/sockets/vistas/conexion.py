"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json
from channels.exceptions import DenyConnection, StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from apps.sockets.vistas.usuario import set_tablero, set_menu_estado, get_contadores, set_tablero_expandido, \
    set_sesion_bloqueada, set_sesion_desbloquear, get_tablerodata, get_notificaciones, get_contador
from modulos.utiles.clases.varios import Dict2Obj


class MadCeroPapelConexion(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'] == AnonymousUser():
            await self.close(code=4123)
            raise DenyConnection("No sesión")
        else:
            self.group_name = 'CnxMad_%s' % self.scope['user'].pk
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            await self.channel_layer.group_send(self.group_name, {'type': data["codigo"], 'data': data})
        except Exception as e:
            print(str(e))

    async def disconnect(self, message):
        # print("Disconnect", message)
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def tablero_orden(self, event):
        await set_tablero(self.scope["user"], event["data"]["orden"])
        await self.send(text_data=json.dumps({
            'codigo': 'ReordenarTablero',
            'tableroorden': event["data"]["orden"]
        }))

    async def menu_abierto(self, event):
        await set_menu_estado(self.scope["user"], event["data"]["estado"])
        await self.send(text_data=json.dumps({
            'ok': True
        }))

    async def documento_generado(self, event):
        await self.send(text_data=json.dumps({
            'codigo': event["data"]["codigo"], 'mensaje': event["data"]["mensaje"]
        }))

    async def documento_firmado(self, event):
        await self.send(text_data=json.dumps({
            'codigo': event["data"]["codigo"],
            'mensaje': event["data"]["mensaje"]
        }))

    async def mad_mensaje(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    async def contadores_actualizar(self, event):
        contadores = await get_contadores(Dict2Obj(self.scope))
        await self.send(text_data=json.dumps({
            'codigo': 'ActualizaContadores',
            'contadores': contadores
        }, ensure_ascii=False))

    async def contador_actualizar(self, event):
        contadores = await get_contador(Dict2Obj(self.scope), event["data"])
        await self.send(text_data=json.dumps({
            'codigo': 'ActualizaContadores',
            'contadores': contadores
        }, ensure_ascii=False))

    async def tablero_expandido(self, event):
        await set_tablero_expandido(event["data"])
        await self.send(text_data=json.dumps({
            'ok': True
        }))

    async def bloquearSesion(self, event):
        await set_sesion_bloqueada(self.scope["user"])
        await self.send(text_data=json.dumps({
            'codigo': 'MostrarBloqueo'
        }))

    async def desbloquearSesion(self, event):
        estado, mensaje = await set_sesion_desbloquear(self.scope["user"], event["data"]["pw"])
        await self.send(text_data=json.dumps({
            'codigo': 'OcultarBloqueo', 'estado': estado, 'mensaje': mensaje, 'ctrl': event["data"]["ctrl"]
        }))

    async def tablero_data(self, event):
        data = await get_tablerodata(Dict2Obj(self.scope), event["data"]["tablero"])
        await self.send(text_data=json.dumps({
            'codigo': 'TableroData',
            'data': data
        }, ensure_ascii=False))

    async def notificaciones(self, event):
        data = await get_notificaciones(Dict2Obj(self.scope))
        await self.send(text_data=json.dumps({
            'codigo': 'Notificaciones',
            'data': data
        }, ensure_ascii=False))
