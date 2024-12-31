"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime

from apps.tramite.models import DestinoEstadoMensajeria
from modulos.utiles.clases.formularios import AppBaseModelForm


class DestinoMensajeriaFinalizarDirectoForm(AppBaseModelForm):
    firstfield = "observacion"

    class Meta:
        model = DestinoEstadoMensajeria
        fields = ["fecha", "observacion"]

    def __init__(self, *args, **kwargs):
        super(DestinoMensajeriaFinalizarDirectoForm, self).__init__(*args, **kwargs)
        self.fields["fecha"].label = "Fecha de Envío"
        self.fields["fecha"].required = True
        self.fields["fecha"].widget.attrs["data-enddate"] = datetime.datetime.now().date().strftime("%Y-%m-%d")
        self.fields["observacion"].label = "Nota"
        self.fields["observacion"].required = True
