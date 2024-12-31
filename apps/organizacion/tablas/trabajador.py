"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from html import escape

from django.urls import reverse

from apps.organizacion.models import PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha, ColumnaAcciones


class ColumnaJefe(Columna):
    def render(self, obj):
        icono = "fas fa-user-tie" if obj.esjefe else (
            "fas fa-user-shield" if obj.esapoyo else "far fa-user")
        color = "default"
        info = ""
        if obj.esapoyo:
            color = "warning"
            info = "Apoyo"
        elif obj.esjefe:
            color = "primary" if obj.esjefemodo == "TI" else "info"
            info = obj.get_esjefemodo_display()
        if len(info) == 0:
            # _result = "<i class='%s text-%s'></i>" % (icono, color)
            _result = ""
        else:
            _result = "<i class='%s text-%s' rel='tooltip' title='%s'></i>" % (icono, color, info)
        if obj.permisotramite == "T":
            _result += "<span class='ml-2' " \
                       "title='Tramitador Documental' rel='tooltip'>" + \
                       "<i class='fas fa-file-import text-%s'></i></span>"
            _result = _result % color
        if obj.esmensajero:
            _result += "<span class='ml-2' " \
                       "title='Mensajero' rel='tooltip'>" + \
                       "<i class='fas fa-motorcycle text-%s'></i></span>"
            _result = _result % color
        if obj.seguimientocompleto:
            _result += "<span class='ml-2' " \
                       "title='Seguimiento Completo' rel='tooltip'>" + \
                       "<i class='fab fa-searchengin text-%s'></span>"
            _result = _result % color
        return _result


class ColumnaDominio(Columna):
    def __init__(self, *args, **kwargs):
        super(ColumnaDominio, self).__init__(
            field="persona.personaconfiguracion.usuariodominio", header="Dominio", position="center"
        )

    def render(self, obj):
        _result = super(ColumnaDominio, self).render(obj)
        if obj.persona.personaconfiguracion.correoinstitucional:
            _result += "<i class='far fa-envelope fa-1x ml-1 text-primary' title='%s' rel='tooltip'></i>" % (
                obj.persona.personaconfiguracion.correoinstitucional
            )
        return escape(_result)


class ColumnaCargo(Columna):
    def render(self, obj):
        return obj.Cargo()


class ColumnaTrabAcciones(Columna):
    def render(self, obj):
        _tpl = "<a data-toggle='modal' data-placement='top' href='%s' data-modal-size='%s' " + \
               "data-target='%s' title='%s' rel='tooltip' " + \
               "class='bs-tooltip btn btn-sm btn-clean btn-icon btn-%s mr-1'>" + \
               "<span class='%s'></span></a>"
        _result = ""
        if obj.tipo in ["NN", "EN", "AP"]:
            # Editar
            _result += _tpl % (
                reverse("apporg:trabajador_editar", kwargs={"pk": obj.pk}),
                "lg", "#modal-principal-centro", "Editar", "default", "flaticon-edit"
            )
            # Eliminar
            _result += _tpl % (
                reverse("apporg:trabajador_eliminar", kwargs={"pk": obj.pk}),
                "lg", "#modal-principal-centro", "Eliminar", "default mr-2", "flaticon-delete"
            )
        # Cambiar Clave
        _result += _tpl % (
            reverse("apporg:trabajador_password", kwargs={"pk": obj.pk}),
            "lg", "#modal-principal-centro",
            "Resetear Contraseña" if obj.persona.usuario else "Asignar Contraseña",
            "outline-primary" if obj.persona.usuario else "default",
            "fas fa-key"
        )
        # Logout
        _result += _tpl % (
            reverse("apporg:trabajador_logout", kwargs={"pk": obj.pk}),
            "lg", "#modal-principal-centro",
            "Cerrar la Sesión del Usuario",
            "outline-info",
            "fas fa-sign-out-alt"
        )
        if obj.tipo in ["NN", "EN", "AP"]:
            # Rotar
            _result += _tpl % (
                reverse("apporg:trabajador_rotar", kwargs={"pk": obj.pk}),
                "lg", "#modal-principal-centro", "Rotar", "outline-warning", "fas fa-sync"
            )
            # Dar de Baja
            _result += _tpl % (
                reverse("apporg:trabajador_baja", kwargs={"pk": obj.pk}),
                "lg", "#modal-centro-scroll", "Dar de Baja", "outline-danger", "fas fa-user-slash"
            )
        #
        return _result


class TablaTrabajadores(Table):
    esjefe = ColumnaJefe(
        field="esjefe", header="", position="center", attrs={"class": "w-80px"}, sortable=False, searchable=False
    )
    usuariodominio = ColumnaDominio()
    documento = Columna(field="persona.numero", header="DNI", position="center")
    persona = Columna(field="persona.apellidocompleto", header="Persona")
    inicio = ColumnaFecha(field="inicio", header="Inicio")
    fin = ColumnaFecha(field="fin", header="Fin")
    cargofull = ColumnaCargo(field="cargo.nombrem", header="Cargo")
    area = Columna(field="area.nombrecorto", header="Unidad Organizacional")
    certificadovence = ColumnaFecha(
        field="persona.personaconfiguracion.certificadovencimiento", header="Certificado", format="%d/%m/%Y %I:%M %p"
    )
    areafull = Columna(field="area.nombre", visible=False)
    cargofem = Columna(field="cargo.nombref", visible=False)
    poscargo = Columna(field="poscargo", visible=False)
    acciones = ColumnaTrabAcciones(
        header="", sortable=False, searchable=False, header_attrs={"class": "text-center"},
        attrs={"class": "text-nowrap text-center"}
    )

    class Meta:
        model = PeriodoTrabajo
        id = "tablaPeriodoTrabajo"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": "#",
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaTrabajadores, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:trabajador_listar", kwargs={"area": 0, "todos": 0})
        self.opts.toolbar[0]["url"] = reverse(viewname="apporg:trabajador_agregar", kwargs={"area": 0})
