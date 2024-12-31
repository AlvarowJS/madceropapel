"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.utils.html import escape

from apps.organizacion.models import Area, PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaEstado(Columna):
    def __init__(self, field):
        super(ColumnaEstado, self).__init__(field=field, header="Estado", position="center")

    def render(self, obj):
        _resp = super(ColumnaEstado, self).render(obj)
        _result = ""
        if not obj.documentoautorizacion and not obj.activo:
            _result = '<span class="label label-light-danger label-inline">PENDIENTE DE FIRMA</span>'
            if obj.Presidentes().order_by("-pk").filter(
                    documentosustento__isnull=False
            ).first().persona == User.objects.get(
                    pk=obj.user_id
            ).persona:
                _result += "<a class='btn btn-outline-danger btn-xs btn-clean btn-icon ml-2 btn-action' " + \
                           "href='javascript:;' title='Firmar' rel='tooltip' data-url='%s'><i class='%s'></i></a>"
                _result = _result % (
                    reverse(viewname="apporg:comision_autorizar_generar", kwargs={"pk": obj.pk}),
                    "fas fa-file-signature"
                )
        else:
            # _result = _result % 'fas fa-check'
            _result = '<span class="label label-light-primary label-inline">APROBADO</span>'
        return escape(_result)


class ColumnaComisionAcciones(Columna):
    def __init__(self):
        super(ColumnaComisionAcciones, self).__init__(
            field="nombre", header="", sortable=False, searchable=False, position="center"
        )

    def render(self, obj):
        _result = ""
        if not obj.documentoautorizacion and not obj.comisiondirecta:
            # Editar
            urledit = reverse("apporg:comision_editar", kwargs={"pk": obj.pk})
            _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                       "data-target='#modal-principal-centro' title='Editar' rel='tooltip' " + \
                       "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                       "<span class='flaticon-edit'></span></a>"
            _result = _result % urledit
            # Eliminar
            urlelimin = reverse("apporg:comision_eliminar", kwargs={"pk": obj.pk})
            _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                       "data-target='#modal-principal-centro' title='Eliminar' rel='tooltip' " + \
                       "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                       "<span class='flaticon-delete'></span></a>"
            _result = _result % urlelimin
        elif obj.jefeactual.persona.usuario.id != obj.user_id:
            # Anular la Solicitud
            nuevopres = obj.trabajadores.filter(
                persona__usuario_id=obj.user_id,
                activo=0
            ).order_by("-creado").first()
            if nuevopres:
                urlelimin = reverse("apporg:comisionsolicitudes_anular", kwargs={"pk": nuevopres.pk})
                _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                           "data-target='#modal-principal-centro' title='Anular' rel='tooltip' " + \
                           "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                           "<span class='fas fa-ban'></span></a>"
                _result = _result % urlelimin
        return _result


class TablaComision(Table):
    nombre = Columna(field="nombre", header="Nombre")
    estado = ColumnaEstado(field="nombre")
    creador = Columna(field="creador.persona.alias", header="Creador", position="center")
    creadoel = ColumnaFecha(field="creado", header="Creado El", format="%d/%m/%Y %I:%M %p")
    accion = ColumnaComisionAcciones()

    class Meta:
        model = Area
        id = "tablaComision"
        toolbar = [
            {
                "id": "btnAddComision",
                "icono": "fa fa-plus",
                "texto": "Agregar Comisión",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apporg:comision_agregar"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            },
        ]

    def __init__(self, *args, **kwargs):
        super(TablaComision, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:comision_listar")


class ColumnaComisionDirectaAcciones(Columna):
    def __init__(self):
        super(ColumnaComisionDirectaAcciones, self).__init__(
            field="nombre", header="", sortable=False, searchable=False, position="center"
        )

    def render(self, obj):
        _result = ""
        # Editar
        urledit = reverse("apporg:comisiondirecta_editar", kwargs={"pk": obj.pk})
        _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                   "data-target='#modal-principal-centro' title='Editar' rel='tooltip' " + \
                   "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                   "<span class='flaticon-edit'></span></a>"
        _result = _result % urledit
        # Eliminar
        urlelimin = reverse("apporg:comisiondirecta_eliminar", kwargs={"pk": obj.pk})
        _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                   "data-target='#modal-principal-centro' title='Eliminar' rel='tooltip' " + \
                   "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                   "<span class='flaticon-delete'></span></a>"
        _result = _result % urlelimin
        return _result


class TablaComisionDirecta(Table):
    nombre = Columna(field="nombre", header="Nombre")
    estado = ColumnaEstado(field="nombre")
    creador = Columna(field="creador.persona.alias", header="Creador", position="center")
    creadoel = ColumnaFecha(field="creado", header="Creado El", format="%d/%m/%Y %I:%M %p")
    accion = ColumnaComisionDirectaAcciones()

    class Meta:
        model = Area
        id = "tablaComisionDirecta"
        toolbar = [
            {
                "id": "btnAddComDirecta",
                "icono": "fa fa-plus",
                "texto": "Agregar Comisión Directa",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apporg:comisiondirecta_agregar"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            },
        ]

    def __init__(self, *args, **kwargs):
        super(TablaComisionDirecta, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:comisiondirecta_listar")


class ColumnaApoyoComisionAcciones(Columna):
    def __init__(self):
        super(ColumnaApoyoComisionAcciones, self).__init__(
            field="persona.apellidocompleto", header="", sortable=False, searchable=False, position="center"
        )

    def render(self, obj):
        _result = ""
        # Editar
        urledit = reverse("apporg:comision_apoyo_editar", kwargs={"pk": obj.pk})
        _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                   "data-target='#modal-principal-centro' title='Editar' rel='tooltip' " + \
                   "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                   "<span class='flaticon-edit'></span></a>"
        _result = _result % urledit
        # Eliminar
        urlelimin = reverse("apporg:comision_apoyo_eliminar", kwargs={"pk": obj.pk})
        _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                   "data-target='#modal-principal-centro' title='Eliminar' rel='tooltip' " + \
                   "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                   "<span class='flaticon-delete'></span></a>"
        _result = _result % urlelimin
        return _result


class TablaApoyoComision(Table):
    numero = Columna(field="persona.numero", header="DNI")
    nombre = Columna(field="persona.apellidocompleto", header="Nombre")
    inicio = ColumnaFecha(field="inicio", header="Desde", format="%d/%m/%Y %I:%M %p")
    fin = ColumnaFecha(field="fin", header="Hasta", format="%d/%m/%Y %I:%M %p")
    creador = Columna(field="creador.persona.alias", header="Creado Por")
    accion = ColumnaApoyoComisionAcciones()

    class Meta:
        model = PeriodoTrabajo
        id = "tablaApoyoComision"
        toolbar = [
            {
                "id": "btnAddApoyo",
                "icono": "fa fa-plus",
                "texto": "Agregar Apoyo",
                # "modal": "#modal-principal-centro",
                "url": "#",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            },
        ]

    def __init__(self, *args, **kwargs):
        super(TablaApoyoComision, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:comision_apoyo_listar", kwargs={"pk": 0})
