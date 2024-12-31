"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models import Q, F
from django.views.generic import FormView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.formularios.documentodetalle import FormDocumentoDestinoGrupo
from apps.tramite.models import TipoTramite, TipoProveido
from apps.tramite.tablas.grupo import TablaDocumentoDestinoGrupo
from modulos.datatable.views import FeedDataView


class DocumentoDestinoGrupo(TemplateValidaLogin, FormView):
    template_name = "tramite/documento/detalles/grupos.html"
    form_class = FormDocumentoDestinoGrupo
    titulo = None

    def get_form(self, form_class=None):
        form = super(DocumentoDestinoGrupo, self).get_form(form_class)
        form.fields["tipotramite"].initial = TipoTramite.objects.get(codigo="0")
        form.fields["proveido"].initial = TipoProveido.objects.filter(pk=1).first()
        return form

    def get_context_data(self, **kwargs):
        context = super(DocumentoDestinoGrupo, self).get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo")
        if tipo == "UO":
            context["titulo"] = "Trabajadores de mi Unidad Organizacional"
            context["TablaDocumentoDestinoGrupo"] = TablaDocumentoDestinoGrupo(tipo)
        return context


class DocumentoDestinoGrupoListar(FeedDataView):
    token = TablaDocumentoDestinoGrupo.token

    def get_queryset(self):
        super(DocumentoDestinoGrupoListar, self).get_queryset()
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        qs = periodoactual.area.TrabajadoresActuales().exclude(
            Q(tipo__in=["EN", "EP"])
            |
            Q(Q(tipo="AP"), ~Q(area=F("persona__ultimoperiodotrabajo__area")))
            |
            Q(esjefe=True)
        ).order_by("persona__apellidocompleto")
        return qs
