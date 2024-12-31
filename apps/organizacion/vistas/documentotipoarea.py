"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Q, Count
from django.views.generic import TemplateView
from django_select2.views import AutoResponseView

from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.documentotipoarea import FormDocumentoTipoAreaSelector, FormDocumentoTipoArea
from apps.organizacion.models import DocumentoTipoArea
from apps.organizacion.tablas.documentotipoarea import TablaDocumentoTipoArea
from modulos.datatable.views import FeedDataView
from modulos.utiles.clases.crud import VistaCreacion, VistaEliminacion


class DocumentoTipoAreaInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/documentotipoarea/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Tipos de Documentos por Unidad Organizacional"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["form"] = FormDocumentoTipoAreaSelector()
        context["tablaDocumentoTipoArea"] = TablaDocumentoTipoArea()
        return self.render_to_response(context=context)


class DocumentoTipoAreaAreasListar(AutoResponseView):
    def get_queryset(self):
        qs = self.widget.filter_queryset(
            self.request,
            self.term,
            self.queryset
        )
        dep = self.request.GET.get("cbtdep")
        if str(dep).startswith("0"):
            qs = qs.exclude(rindentepadre__isnull=False)  # .exclude(esrindente=True)
        elif dep:
            qs = qs.filter(rindentepadre_id=int(dep))
        return qs


class DocumentoTipoAreaListar(FeedDataView):
    token = TablaDocumentoTipoArea.token

    def get_queryset(self):
        qs = super(DocumentoTipoAreaListar, self).get_queryset()
        qs = qs.filter(
            area_id=self.kwargs.get("area")
        )
        return qs


class DocumentoTipoAreaAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "organizacion/documentotipoarea/formulario.html"
    model = DocumentoTipoArea
    form_class = FormDocumentoTipoArea
    
    def get_context_data(self, **kwargs):
        context = super(DocumentoTipoAreaAgregar, self).get_context_data(**kwargs)
        if self.kwargs.get("area") == 0:
            context["noarea"] = True
            context["noBotonGuardar"] = True
            context["botoncancelartexto"] = "Aceptar"
        return context

    def get_form(self, form_class=None):
        form = super(DocumentoTipoAreaAgregar, self).get_form(form_class)
        if self.kwargs.get("area") > 0:
            form.fields["tiposdocumentos"].queryset = form.fields["tiposdocumentos"].queryset.annotate(
                plantillas=Count(
                    "documentotipoplantilla",
                    filter=Q(documentotipoplantilla__dependencia__codigo=settings.CONFIG_APP["Dependencia"])
                )
            ).filter(
                Q(plantillaautomatica=True)
                |
                Q(plantillas__gt=0)
            ).exclude(
                pk__in=DocumentoTipoArea.objects.filter(
                    area_id=self.kwargs.get("area")
                ).values_list("documentotipo_id")
            )
        return form

    def form_valid(self, form):
        if form.is_valid():
            cldt = form.cleaned_data
            for tipodoc in cldt["tiposdocumentos"]:
                dta = DocumentoTipoArea(
                    area_id=self.kwargs.get("area"),
                    documentotipo=tipodoc,
                    creador=self.request.user
                )
                dta.save()
        return self.render_to_response(self.get_context_data(form=form))


class DocumentoTipoAreaEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "organizacion/documentotipoarea/eliminar.html"
    model = DocumentoTipoArea
