"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import F
from django.urls import reverse
from django.utils.html import escape

from apps.organizacion.models import PeriodoTrabajo
from apps.tramite.managers import am_documento_siglas, am_documento_nro
from apps.tramite.models import Destino, Documento, DocumentoFirma, CargoExternoDetalle, AnexoFirma, DocumentoEstado
from modulos.datatable.columns.basecolumn import Columna


class ColumnaBandejaConfidencial(Columna):
    def __init__(self, field, *args, **kwargs):
        super(ColumnaBandejaConfidencial, self).__init__(
            field=field,
            header="",
            header_attrs={"class": "text-center nowrap w-25px"},
            attrs={"class": "text-center"},
            sortable=False,
            searchable=False,
            visible=True,
            position="center"
        )

    def render(self, obj):
        _result = ""
        objeto = obj
        if isinstance(obj, Destino):
            objeto = obj.documento
        elif isinstance(obj, DocumentoFirma):
            objeto = obj.documento
        elif isinstance(obj, CargoExternoDetalle):
            objeto = obj.destino.documento
        elif isinstance(obj, AnexoFirma):
            objeto = obj.anexo.documento
        if objeto.confidencial:
            _result = "<i class='fas fa-lock fa-1x text-danger' title='Confidencial' rel='tooltip'></i>"
        return _result


class ColumnaBandejaSeguimiento(Columna):
    def __init__(self, field, *args, **kwargs):
        super(ColumnaBandejaSeguimiento, self).__init__(
            field=field,
            header="",
            header_attrs={"class": "text-center nowrap w-25px"},
            attrs={"class": "text-center"},
            sortable=False,
            searchable=False,
            visible=True,
            position="center"
        )

    def render(self, obj):
        modo = "X"
        exp = None
        objeto = obj
        doc = obj
        if isinstance(obj, Documento):
            objeto = obj
            modo = "DOC"
            exp = obj.expediente
        elif isinstance(obj, Destino):
            doc = obj.documento
            objeto = obj
            modo = "DES"
            exp = obj.documento.expediente
        elif isinstance(obj, DocumentoFirma):
            objeto = obj.documento
            doc = obj.documento
            modo = "DOC"
            exp = obj.documento.expediente
        elif isinstance(obj, CargoExternoDetalle):
            doc = obj.destino.documento
            objeto = obj.destino
            modo = "DES"
            exp = obj.destino.documento.expediente
        _result = ""
        if exp:
            if doc.ultimoestado.estado != "AN":
                _result = '<a href="javascript:;" class="btn btn-xs btn-light-primary btn-icon" rel="tooltip" ' \
                          'title="Seguimiento"%s>' \
                          '<i class="la la-search"></i>' \
                          '</a>'
                if settings.CONFIG_APP.get("Seguimiento"):
                    _result = _result % (
                            " data-seg='%s' data-modo='%s' data-origen='bandeja'" % (objeto.pk, modo)
                    )
                else:
                    _result = _result % ""
        return _result


class ColumnaExpediente(Columna):
    def __init__(self, field, tab, openin="OF", enlace=True):
        super(ColumnaExpediente, self).__init__(field=field, header="Expediente", position="center")
        self.tab = tab
        self.enlace = enlace
        self.openin = openin

    def render(self, obj):
        _result = super(ColumnaExpediente, self).render(obj)
        objtab = obj
        if hasattr(obj, "anexo"):
            obj = obj.anexo
        if hasattr(obj, "documento"):
            obj = obj.documento
        if _result == "--":
            _result = "<i class='far fa-question-circle'></i>"
        if self.enlace:
            if self.openin == "OF":  # obj.origentipo in ["O", "P"]:
                _urledit = "apptra:documento_emitir_editar"
                kwargs = {
                    "pk": obj.pk,
                    "tab": self.tab,
                    "tabid": objtab.pk
                }
            else:
                _urledit = "apptra:mesapartes_registrar_editar"
                kwargs = {
                    "pk": obj.pk
                }
            _result = "<a href='%s' class='btn btn-sm btn-text-primary btn-hover-light-primary py-1' " \
                      "data-toggle='modal' data-target='#modal-principal' data-modal-size='xl'>%s</a>" % (
                          reverse(viewname=_urledit, kwargs=kwargs),
                          _result
                      )
        return _result


class ColumnaDocumento(Columna):
    def __init__(self, field, modo=2, vermodo=True):
        super(ColumnaDocumento, self).__init__(field=field, header="Documento")
        self.modo = modo
        self.vermodo = vermodo

    def render(self, obj):
        _result = super(ColumnaDocumento, self).render(obj)
        objact = obj
        objtab = obj
        if hasattr(obj, "anexo"):
            obj = obj.anexo
        if hasattr(obj, "documento"):
            obj = obj.documento
        if isinstance(obj, CargoExternoDetalle):
            objtab = obj.destino
            obj = obj.destino.documento
        # if ((obj.confidencial and
        #     (obj.origentipo == "O" and
        #      (objact.esjefe or objact.esencargado or obj.emisor.pk == objact.trabajadoractual)
        #     ) or
        #     (obj.origentipo == "P" and obj.emisor.pk == objact.trabajadoractual)) or not obj.confidencial) and \
        #         obj.documentoplantilla.documentopdf_set.count() > 0:
        if obj.documentoplantilla.documentopdf_set.count() > 0:
            if obj.documentotipoarea.documentotipo.esmultiple and \
                    not obj.documentotipoarea.documentotipo.esmultipledestino and \
                    obj.forma == "I":
                if isinstance(objtab, Documento):
                    urldown = reverse(viewname='apptra:documento_descargar_2',
                                      kwargs={"ori": "documento", "cod": objtab.pk})
                    _result = '<a class="text-wrap btn-hover-light-primary puntero" data-toggle="modal" ' \
                              'href="%s" data-target="#modal-pdf-viewer-full" data-modal-size="xl">%s</a>' % (
                                  urldown,
                                  _result
                              )
                else:
                    urldown = reverse('apptra:documento_descargar_2', kwargs={
                        'ori': 'destino',
                        'cod': objtab.pk
                    })
                    cadenaUrl = '%s%s' % (
                        "$('#modal-pdf-viewer-full .modal-content').load('" + urldown + "');",
                        "$('#modal-pdf-viewer-full').modal('show');"
                    )
                    _result = '<a class="text-wrap btn-hover-light-primary puntero" ' \
                              'onclick="%s">%s</a>' % (
                                  cadenaUrl,
                                  _result
                              )
            else:
                oridoc = type(objtab).__name__.lower()
                urldown = reverse(viewname='apptra:documento_descargar_2', kwargs={"ori": oridoc, "cod": objtab.pk})
                _result = '<a class="text-wrap btn-hover-light-primary puntero" data-toggle="modal" ' \
                          'href="%s" data-target="#modal-pdf-viewer-full" data-modal-size="xl">%s</a>' % (
                              urldown,
                              _result
                          )
            if isinstance(obj, Documento) and self.vermodo:
                if obj.origentipo in ["F", "V"]:
                    modo = "<span class='label label-sm mr-1 label-light-grey' rel='tooltip' " + \
                           "title='%s'>%s</span>"
                    _result = "%s %s" % (
                        modo % (obj.get_origentipo_display(), obj.origentipo),
                        _result
                    )
        return escape(_result)


class ColumnaAsunto(Columna):
    def __init__(self, field):
        super(ColumnaAsunto, self).__init__(field=field, header="Asunto")

    def render(self, obj):
        if hasattr(obj, "anexo"):
            obj = obj.anexo
        if hasattr(obj, "documento"):
            obj = obj.documento
        if obj.confidencial and obj.esapoyo and obj.creador != obj.usuarioactual:
            return "CONFIDENCIAL"
        else:
            return obj.asuntocorto


class ColumnaDestinoEstado(Columna):
    def __init__(self):
        super(ColumnaDestinoEstado, self).__init__(
            field="ultimoestado.estado", header="Estado", position="center", header_attrs={"width": "56px"}
        )

    def render(self, obj):
        color = "danger" if obj.ultimoestado.estado == "NL" else "primary"
        estado = obj.ultimoestado.get_estado_display()
        if obj.destinoreferencias.exclude(documento__ultimoestado__estado__in=["AN"]).count() > 0 and \
                obj.ultimoestado.estado == "RE":
            atendidocon = obj.destinoreferencias.exclude(documento__ultimoestado__estado__in=["AN"]).annotate(
                documentoid=F("documento__pk"),
                documentonro=am_documento_nro("documento"),
                documentonrosiglas=am_documento_siglas("documento"),
                documentoasunto=F("documento__asunto"),
                documentoestado=F("documento__ultimoestado__estado"),
                documentoforma=F("documento__origentipo"),
            ).values(
                "documentoid", "documentonrosiglas", "documentoasunto", "documentoestado",
                "documentoforma"
            ).first()
            color = "warning"
            estado = "En Atención"
            atenciontexto = "<div class='font-weight-bold'>%s</div><div>%s</div>" % (
                atendidocon["documentonrosiglas"],
                escape(atendidocon["documentoasunto"])
            )
            atenciontitulo = "Bandeja: <span class='text-primary'>%s %s</span>" % (
                dict(DocumentoEstado.ESTADO)[atendidocon["documentoestado"]].upper(),
                "OFICINA" if atendidocon["documentoforma"] == "O" else "PERSONAL"
            )
            _result = '<span class="label label-outline-%s label-inline" title="%s" data-toggle="popover" ' \
                      'data-content="%s" data-html="true">' \
                      '%s</span>'
            _result = _result % (
                color,
                atenciontitulo,
                atenciontexto,
                estado
            )
        else:
            _result = '<span class="label label-outline-%s label-inline">%s</span>' % (
                color,
                estado
            )
        if obj.ultimoestado.observacion and obj.ultimoestado.estado == "RH":
            _result += '<span class="label label-outline-%s label-inline mt-1" rel="tooltip" title="%s" >%s</span>'
            _result = _result % (
                'info',
                obj.ultimoestado.observacion,
                'Observado'
            )
        return escape(_result)


class ColumnaInformacionFisica(Columna):
    def __init__(self):
        super(ColumnaInformacionFisica, self).__init__(
            field="documentacionfisica", header="", position="center", searchable=False, sortable=False
        )

    def render(self, obj):
        _result = ""
        if obj.entregafisicareceptor:
            _result = "<a class='btn btn-icon btn-xs btn-primary' title='Información Física Recepcionada' " \
                      "rel='tooltip' href='javascript:;' " \
                      "onclick='viewPDF(\"%s\", \"%s\", \"%s\")'>" \
                      "<i class='flaticon-file-2'></i></a>"
            _result = _result % (
                reverse('apptra:documento_recfis_doc', kwargs={"doc": obj.documento.pk, "des": obj.pk}),
                obj.documento.nombreDocumentoNumero(),
                obj.token
            )
        return _result
