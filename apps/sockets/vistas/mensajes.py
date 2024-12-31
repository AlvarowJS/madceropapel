"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import channels.layers
from asgiref.sync import async_to_sync


def SocketMsg(userid, funcpost, tipo=None, clase=None, icono=None, titulo=None, mensaje=None):
    channel_layer = channels.layers.get_channel_layer()
    tipo = tipo or ""
    clase = clase or ""
    icono = icono or ""
    titulo = titulo or ""
    mensaje = mensaje or ""
    async_to_sync(channel_layer.group_send)(
        'CnxMad_%s' % userid, {
            'type': 'mad.mensaje',
            'data': {
                'codigo': 'Msg',
                'tipo': tipo,
                'clase': clase,
                'icono': icono,
                'titulo': titulo,
                'mensaje': mensaje,
                'funcpost': funcpost
            }
        }
    )


def SocketDocGen(modo, userid, mensaje):
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'CnxMad_%s' % userid,
        {
            'type': 'documento.generado',
            'data': {
                'codigo': 'DocGen' + modo,
                'mensaje': mensaje
            }
        }
    )


def SocketDocFir(modo, userid, mensaje):
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'CnxMad_%s' % userid,
        {
            'type': 'documento.firmado',
            'data': {
                'codigo': 'DocFir' + modo,
                'mensaje': mensaje
            }
        }
    )
