"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import escape

from apps.organizacion.models import PeriodoTrabajo
from modulos.datatable import Table
from modulos.datatable.columns.basecolumn import Columna, ColumnaFecha


class ColumnaDoc(Columna):
    def __init__(self, field=None, *args, **kwargs):
        super(ColumnaDoc, self).__init__(field=field, header="Sustento", *args, **kwargs)

    def render(self, obj):
        _result = ""
        if obj.documentosustento:
            _result = "<a href='javascript:;' onclick='viewPDF(\"%s\", \"%s\", \"%s\")'>%s</a>"

            _result = _result % (
                reverse("apptra:documento_descargar", kwargs={"pk": obj.documentosustento.pk}),
                obj.documentosustento.obtenerNumeroSiglas(),
                obj.creador.auth_token.key,
                obj.documentosustento.obtenerNumeroSiglas()
            )
        return _result


class ColumnaDocCargo(Columna):
    def __init__(self, field=None, *args, **kwargs):
        super(ColumnaDocCargo, self).__init__(
            field=field, header="Cargo", header_attrs={"width": "60px"}, *args, **kwargs
        )

    def render(self, obj):
        _result = ""
        if obj.encargaturaplantilla:
            _result += "<a class='btn btn-icon btn-light-success btn-circle btn-xs' title='Cargo Firmado' " \
                       "rel='tooltip' href='javascript:;' " \
                       "onclick='viewPDF(\"%s\", \"%s\", \"%s\")'>" \
                       "<i class='flaticon2-sheet'></i></a>"
            _result = _result % (
                reverse('apporg:encargatura_cargo_doc', kwargs={"pk": obj.pk}),
                "Encargatura",
                obj.token
            )
        if obj.encargaturaplantillaanulacion:
            _result += "<a class='btn btn-icon btn-light-danger btn-circle btn-xs ml-2' title='Cargo Anulación' " \
                       "rel='tooltip' href='javascript:;' " \
                       "onclick='viewPDF(\"%s\", \"%s\", \"%s\")'>" \
                       "<i class='flaticon2-sheet'></i></a>"
            _result = _result % (
                reverse('apporg:encargatura_cargo_docanu', kwargs={"pk": obj.pk}),
                "Encargatura Anulación",
                obj.token
            )
        return _result


class ColumnaAccion(Columna):
    def __init__(self):
        super(ColumnaAccion, self).__init__(
            field="persona.numero", header="Acción", sortable=False, searchable=False, position="center",
            header_attrs={"width": "90px"}
        )

    def render(self, obj):
        _result = ""
        fechaActual = timezone.now()
        if fechaActual < obj.fin:
            if not obj.encargaturaplantilla:
                _result += "<a class='btn btn-icon btn-xs btn-circle btn-primary btn-action' " + \
                           "title='Firmar Autorización' rel='tooltip' data-url='%s' href='javascript:;'>" + \
                           "<i class='fas fa-file-signature'></i></a>"
                _result = _result % (
                    reverse("apporg:encargatura_firmar", kwargs={"pk": obj.pk})
                )
            elif not obj.encargaturaplantillaanulacion:
                _result += "<a class='btn btn-icon btn-xs btn-circle btn-danger btn-action' " + \
                           "title='Anular Autorización' rel='tooltip' data-url='%s' href='javascript:;'>" + \
                           "<i class='fas fa-handshake-slash'></i></a>"
                _result = _result % (
                    reverse("apporg:encargatura_anular", kwargs={"pk": obj.pk})
                )
            if not obj.encargaturaplantilla and not obj.encargaturaplantillaanulacion:
                # Editar
                _result += "<a class='btn btn-icon btn-xs btn-circle btn-info ml-2' " + \
                           "title='Modificar Encargatura' rel='tooltip' href='%s' data-toggle='modal' " + \
                           "data-target='#modal-principal-centro' data-modal-size='lg'>" + \
                           "<i class='far fa-edit'></i></a>"
                _result = _result % (
                    reverse("apporg:encargatura_editar", kwargs={"pk": obj.pk})
                )
                # Eliminar
                _result += "<a class='btn btn-icon btn-xs btn-circle btn-danger ml-2' " + \
                           "title='Eliminar Encargatura' rel='tooltip' href='%s' data-toggle='modal' " + \
                           "data-target='#modal-principal-centro'>" + \
                           "<i class='fas fa-trash'></i></a>"
                _result = _result % (
                    reverse("apporg:encargatura_eliminar", kwargs={"pk": obj.pk})
                )
        return _result


class TablaEncargatura(Table):
    dni = Columna(field="persona.numero", header="DNI", position="center")
    persona = Columna(field="persona.apellidocompleto", header="Persona")
    inicio = ColumnaFecha(field="inicio", header="Inicio", format="%d/%m/%Y %I:%M %p")
    fin = ColumnaFecha(field="fin", header="Fin", format="%d/%m/%Y %I:%M %p")
    area = Columna(field="area.nombrecorto", header="Unidad Organizacional")
    documento = ColumnaDoc(field="documentosustento.numero")
    documentoCargo = ColumnaDocCargo(field="encargaturaplantilla", position="center")
    estado = Columna(field="encargaturaestado", header="Estado", position="center")
    acciones = ColumnaAccion()

    class Meta:
        model = PeriodoTrabajo
        id = "tablaEncargatura"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apporg:encargatura_agregar"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaEncargatura, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:encargatura_listar")


class ColumnaAccionPuesto(Columna):
    def __init__(self):
        super(ColumnaAccionPuesto, self).__init__(
            field="persona.numero", header="Acción", sortable=False, searchable=False, position="center"
        )

    def render(self, obj):
        _result = ""
        if not obj.fin:
            _result += "<a class='btn btn-icon btn-xs btn-circle btn-primary btn-action' data-toggle='modal' " + \
                       "title='Terminar Encargatura de Puesto' rel='tooltip' href='%s' " + \
                       "data-target='#modal-principal-centro'>" + \
                       "<i class='flaticon2-cancel'></i></a>"
            _result = _result % (
                reverse("apporg:encargaturapuesto_terminar", kwargs={"pk": obj.pk})
            )
        return _result


class ColumnaTachar(Columna):
    def render(self, obj):
        result = super(ColumnaTachar, self).render(obj)
        if not obj.activo:
            result = "<del class='opacity-50'>%s</del>" % result
            result = escape(result)
        return result


class TablaEncargaturaPuesto(Table):
    dni = ColumnaTachar(field="persona.numero", header="DNI", position="center")
    persona = ColumnaTachar(field="persona.apellidocompleto", header="Persona")
    inicio = ColumnaFecha(field="inicio", header="Inicio", format="%d/%m/%Y %I:%M %p")
    fin = ColumnaFecha(field="fin", header="Fin", format="%d/%m/%Y %I:%M %p")
    area = ColumnaTachar(field="area.nombre", header="Unidad Organizacional")
    estado = Columna(field="encargaturaestado", header="Estado", position="center")
    creador = Columna(field="creador.persona.alias", header="Creador", position="center")
    acciones = ColumnaAccionPuesto()

    class Meta:
        model = PeriodoTrabajo
        id = "tablaEncargaturaPuesto"
        toolbar = [
            {
                "id": "btnAdd",
                "icono": "fa fa-plus",
                "texto": "Agregar",
                "modal": "#modal-principal-centro",
                "url": reverse_lazy("apporg:encargaturapuesto_agregar"),
                "attrs": {
                    "data-modal-size": "lg",
                    "campo": "1"
                }
            }
        ]

    def __init__(self, *args, **kwargs):
        super(TablaEncargaturaPuesto, self).__init__(*args, **kwargs)
        self.opts.ajax_source = reverse(viewname="apporg:encargaturapuesto_listar")
