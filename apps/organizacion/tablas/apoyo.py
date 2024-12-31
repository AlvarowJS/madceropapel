"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from pytz import timezone as pytz_timezone

from apps.organizacion.models import PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaDoc(Columna):
    def __init__(self, field=None, *args, **kwargs):
        super(ColumnaDoc, self).__init__(field=field, header="Documento Sustento", *args, **kwargs)

    def render(self, obj):
        _result = ""
        if obj.documentosustento:
            _result = "<a href='javascript:;' onclick='viewPDF(\"%s\", \"%s\", \"%s\")'>%s</a>"

            _result = _result % (
                reverse("apptra:documento_descargar", kwargs={"pk": obj.documentosustento.pk}),
                obj.documentosustento.nombreDocumentoNumero(),
                obj.creador.auth_token.key,
                obj.documentosustento.nombreDocumentoNumero()
            )
        return _result


class ColumnaAccion(Columna):
    def __init__(self):
        super(ColumnaAccion, self).__init__(
            field="persona.numero", header="Acción", sortable=False, searchable=False, position="center",
            header_attrs={"width": "60px"}
        )

    def render(self, obj):
        _result = ""
        # fechaActual = timezone.localdate(timezone.now())
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        if obj.fin and fechaActual < obj.fin:
            user = User.objects.get(pk=obj.userid)
            if not obj.aprobador:
                if (obj.creador.pk == obj.userid or
                        obj.creador.persona.ultimoperiodotrabajo.area == user.persona.ultimoperiodotrabajo.area):
                    # Editar
                    _result += "<a class='btn btn-icon btn-xs btn-circle btn-info ml-2' " + \
                               "title='Modificar Apoyo' rel='tooltip' href='%s' data-toggle='modal' " + \
                               "data-target='#modal-principal-centro' data-modal-size='lg'>" + \
                               "<i class='far fa-edit'></i></a>"
                    _result = _result % (
                        reverse("apporg:apoyo_editar", kwargs={"pk": obj.pk})
                    )
                    # Eliminar
                    _result += "<a class='btn btn-icon btn-xs btn-circle btn-danger ml-2' " + \
                               "title='Eliminar Apoyo' rel='tooltip' href='%s' data-toggle='modal' " + \
                               "data-target='#modal-principal-centro'>" + \
                               "<i class='fas fa-trash'></i></a>"
                    _result = _result % (
                        reverse("apporg:apoyo_eliminar", kwargs={"pk": obj.pk})
                    )
                if ((user.persona.ultimoperiodotrabajo.esjefe and
                     obj.apoyoarea == user.persona.ultimoperiodotrabajo.area) or
                        (
                                user.persona.ultimoperiodotrabajo.Encargaturas().filter(
                                    area=obj.apoyoarea, esjefe=True
                                ).count() > 0
                        )
                ):
                    # Firmar
                    _result += "<a class='btn btn-icon btn-xs btn-circle btn-danger ml-2' " + \
                               "title='Autorizar' rel='tooltip' href='%s' data-toggle='modal' " + \
                               "data-target='#modal-principal-centro'>" + \
                               "<i class='fas fa-file-signature'></i></a>"
                    _result = _result % (
                        reverse("apporg:apoyo_autorizar", kwargs={"pk": obj.pk})
                    )
        return _result


class TablaApoyo(Table):
    area = Columna(field="apoyoarea.nombre", header="Area")
    persona = Columna(field="persona.apellidocompleto", header="Persona")
    apoyoforma = Columna(field="apoyoforma", header="Forma")
    inicio = ColumnaFecha(field="inicio", header="Inicio", format="%d/%m/%Y %I:%M %p")
    fin = ColumnaFecha(field="fin", header="Fin", format="%d/%m/%Y %I:%M %p")
    estado = Columna(field="encargaturaestado", header="Estado", position="center")
    solicitante = Columna(field="area.nombre", header="Solicitante", position="center")
    acciones = ColumnaAccion()

    class Meta:
        model = PeriodoTrabajo
        id = "tablaApoyo"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apporg:apoyo_agregar"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaApoyo, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:apoyo_listar")
