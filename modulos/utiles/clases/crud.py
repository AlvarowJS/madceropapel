"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from urllib.parse import urlsplit

from django.db.models import ProtectedError
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView


class AuditableMixin(object, ):
    def form_valid(self, form):
        if not form.instance.pk:
            if not hasattr(form.instance, "creador"):
                form.instance.creador = self.request.user
        else:
            form.instance.editor = self.request.user
        return super(AuditableMixin, self).form_valid(form)


class ValidarModal(object, ):
    permitir_desde = None

    def render_to_response(self, context, **response_kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponse("<script>window.location.reload();</script>")
        else:
            _esquema = urlsplit(self.request.build_absolute_uri(None)).scheme
            _host = self.request.get_host()
            _padre = self.request.META.get("HTTP_REFERER", "").lower()
            _actual = self.request.path.lower()
            _padre = _padre.replace(_esquema + "://", "")
            _padre = _padre.replace(_host, "")
            _permitir = False
            if [ele for ele in ["127.0.0.1", ".ngrok.io"] if (ele in _host)]:
                _permitir = True
            else:
                if self.permitir_desde:
                    if isinstance(self.permitir_desde, bool):
                        _permitir = self.permitir_desde
                    if isinstance(self.permitir_desde, str) and _padre == self.permitir_desde:
                        _permitir = True
                    if isinstance(self.permitir_desde, list) and _padre in self.permitir_desde:
                        _permitir = True
                if not _permitir and len(_padre) > 0 and _actual.startswith(_padre):
                    _permitir = True
                if not _permitir:
                    self.template_name = "inicio/blanco.html"
        tpl = super(ValidarModal, self).render_to_response(context, **response_kwargs)
        return tpl


class VistaCreacionMaster(CreateView):
    def get_context_data(self, **kwargs):
        context = super(VistaCreacionMaster, self).get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.save()
            self.object = form.instance
        return self.render_to_response(self.get_context_data(form=form))


class VistaCreacion(AuditableMixin, ValidarModal, VistaCreacionMaster):
    pass


class VistaEdicionMaster(UpdateView):
    def get_form_kwargs(self):
        kwargs = super(VistaEdicionMaster, self).get_form_kwargs()
        kwargs["kwargs"] = self.kwargs
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        if form.is_valid():
            form.save()
            self.object = form.instance
        return self.render_to_response(self.get_context_data(form=form))


class VistaEdicion(AuditableMixin, ValidarModal, VistaEdicionMaster):
    pass


class VistaEliminacionMaster(DeleteView):
    success_url = reverse_lazy("appini:inicio_blank")

    def get_context_data(self, **kwargs):
        context = super(VistaEliminacionMaster, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Eliminar"
        return context

    def form_valid(self, form):
        try:
            _result = super(VistaEliminacionMaster, self).form_valid(form)
        except ProtectedError as e:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            context["errordelete"] = "El registro no puede ser eliminado"
            _result = self.render_to_response(context)
        return _result


class VistaEliminacion(ValidarModal, VistaEliminacionMaster):
    pass
