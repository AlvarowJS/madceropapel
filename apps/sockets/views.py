"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.shortcuts import render


# Create your views here.
async def websocket_view(socket):
    await socket.accept()
    await socket.send_text('hello')
    await socket.close()
