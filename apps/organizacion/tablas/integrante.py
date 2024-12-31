"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import escape

from apps.organizacion.models import PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha, ColumnaBoolean


class ColumnaTachar(Columna):
    def render(self, obj):
        _result = super(ColumnaTachar, self).render(obj)
        if not obj.area.documentoautorizacion:
            _result = "<span>%s</span>" % _result
        elif not obj.activo:
            if obj.cargo.esprincipal and not obj.aprobador:
                _result = "<span class='text-success'>%s</span>" % _result
            else:
                _result = "<del class='text-muted'>%s</del>" % _result

        return escape(_result)


class ColumnaIntegranteAcciones(Columna):
    def __init__(self):
        super(ColumnaIntegranteAcciones, self).__init__(
            field="inicio", sortable=False, searchable=False, position="center", header="",
            header_attrs={"style": "width:70px"}
        )

    def render(self, obj):
        _result = ""
        userActual = User.objects.get(pk=obj.user_id)
        if not obj.area.documentoautorizacion:
            if not obj.cargo.esprincipal:
                # Editar
                urledit = reverse("apporg:integrantedirecta_editar", kwargs={"pk": obj.pk})
                _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                           "data-target='#modal-principal-centro' title='Editar' rel='tooltip' " + \
                           "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                           "<span class='flaticon-edit'></span></a>"
                _result = _result % urledit
                # Eliminar
                urlelimin = reverse("apporg:integrantedirecta_quitar", kwargs={"pk": obj.pk})
                _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                           "data-target='#modal-principal-centro' title='Quitar' rel='tooltip' " + \
                           "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                           "<span class='flaticon-delete'></span></a>"
                _result = _result % urlelimin
        else:
            if not obj.activo and not obj.aprobador and not obj.fin and (
                    obj.creador == userActual or obj.area.jefeactual.persona.usuario == userActual or
                    obj.creador.persona.ultimoperiodotrabajo.area == userActual.persona.ultimoperiodotrabajo.area or
                    obj.area.jefeactual.persona.ultimoperiodotrabajo.area ==
                    userActual.persona.ultimoperiodotrabajo.area
            ):
                # Eliminar
                urlelimin = reverse("apporg:integrante_quitar", kwargs={"pk": obj.pk})
                _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                           "data-target='#modal-principal-centro' title='Quitar' rel='tooltip' " + \
                           "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                           "<span class='flaticon-delete'></span></a>"
                _result = _result % urlelimin
            elif obj.activo and obj.aprobador and \
                    userActual.persona.ultimoperiodotrabajo.area == \
                    obj.area.jefeactual.persona.ultimoperiodotrabajo.area:
                if (not obj.cargo.esprincipal) or (obj.cargo.esprincipal and obj.area.trabajadores.filter(
                        cargo__esprincipal=True, aprobador__isnull=True, fin=None
                ).count() == 0):
                    tipointegrante = "Presidente" if obj.cargo.esprincipal else "Integrante"
                    iconointegrante = "flaticon2-user" if obj.cargo.esprincipal else "flaticon-users-1"
                    urlcambio = reverse("apporg:integrante_cambiar", kwargs={"pk": obj.pk})
                    _result += "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='lg' " + \
                               "data-target='#modal-principal-centro' title='Cambiar %s' rel='tooltip' " + \
                               "class='bs-tooltip btn btn-sm btn-clean btn-icon mr-1'>" + \
                               "<span class='%s'></span></a>"
                    _result = _result % (urlcambio, tipointegrante, iconointegrante)
        return _result


class TablaIntegrante(Table):
    estado = ColumnaBoolean(field="activo", header="Estado", choices=((True, "Activo"), (False, "Inactivo")))
    cargo = ColumnaTachar(field="cargo.nombref", header="Rol", displaytext="Cargo")
    nombre = ColumnaTachar(field="persona.apellidocompleto", header="Nombre")
    inicio = ColumnaFecha(field="inicio", header="Inicio", format="%d/%m/%Y")
    fin = ColumnaFecha(field="fin", header="Fin", format="%d/%m/%Y")
    documento = Columna(
        field="documentosustento.numero", header="Sustento", displaytext="documentosustento.nombreDocumentoNumero"
    )
    creador = Columna(field="creador.persona.alias", header="Creador", position="center")
    accion = ColumnaIntegranteAcciones()

    class Meta:
        model = PeriodoTrabajo
        id = "tablaIntegrante"
        toolbar = [
            {
                "id": "btnAddIntegrante",
                "icono": "fa fa-plus",
                "texto": "Agregar Integrante",
                "modal": "#modal-principal-centro",
                "url": "",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaIntegrante, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:integrante_listar", kwargs={"comid": 0})
        self.opts.toolbar[0]["url"] = reverse(viewname="apporg:integrante_agregar", kwargs={"comid": 0})


class TablaIntegranteDirecta(Table):
    cargo = ColumnaTachar(field="cargo.nombref", header="Rol", displaytext="Cargo")
    nombre = ColumnaTachar(field="persona.apellidocompleto", header="Nombre")
    inicio = ColumnaFecha(field="inicio", header="Inicio", format="%d/%m/%Y")
    fin = ColumnaFecha(field="fin", header="Fin", format="%d/%m/%Y")
    creador = Columna(field="creador.persona.alias", header="Creador", position="center")
    accion = ColumnaIntegranteAcciones()

    class Meta:
        model = PeriodoTrabajo
        id = "tablaIntegranteDirecta"
        toolbar = [
            {
                "id": "btnAddDir",
                "icono": "fa fa-plus",
                "texto": "Agregar Integrante Directo",
                "modal": "#modal-principal-centro",
                "url": "",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaIntegranteDirecta, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:integrantedirecta_listar", kwargs={"comid": 0})
        self.opts.toolbar[0]["url"] = reverse(viewname="apporg:integrantedirecta_agregar", kwargs={"comid": 0})
