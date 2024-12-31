"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import F
from django.views.generic import TemplateView, DetailView

from apps.inicio.models import Distrito
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.organizacion.formularios.area import FormArea, FormAreaActivar, FormAreaMover
from apps.organizacion.models import Area, Dependencia, AreaTipo
from modulos.utiles.clases.crud import VistaCreacion, VistaEdicion, VistaEliminacion


class AreaInicio(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/area/vista.html"
    http_method_names = "post"
    extra_context = {
        "tituloPagina": "Unidades Organizacionales"
    }

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context["tipos"] = AreaTipo.objects.filter(paracomision=False)
        return self.render_to_response(context=context)


class AreaListar(TemplateValidaLogin, TemplateView):
    template_name = "organizacion/area/lista.html"
    http_method_names = "post"
    content_type = "application/json"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        idpadre = request.POST.get("parent")
        idpadre = None if idpadre == '#' else int(idpadre)
        areas = Area.objects.filter(
            dependencia__codigo=settings.CONFIG_APP["Dependencia"],
            padre_id=idpadre
        ).exclude(
            paracomisiones=True
        ).order_by(
            "orden"
        )
        context["areas"] = areas
        return self.render_to_response(context=context)


class AreaAgregar(TemplateValidaLogin, VistaCreacion):
    template_name = "organizacion/area/formulario.html"
    model = Area
    form_class = FormArea

    def get_form(self, form_class=None):
        form = super(AreaAgregar, self).get_form(form_class)
        del form.fields["mensajeriaambito"]
        del form.fields["mensajeriadistritosl"]
        return form

    def form_valid(self, form):
        if form.is_valid():
            form.instance.padre_id = self.kwargs.get("padre", None)
            super(AreaAgregar, self).form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))


class AreaEditar(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/area/formulario.html"
    model = Area
    form_class = FormArea

    def get_form(self, form_class=None):
        form = super(AreaEditar, self).get_form(form_class)
        form.fields["mensajeriadistritosl"].initial = Distrito.objects.filter(
            pk__in=eval(self.get_object().mensajeriadistritos or "[]")
        )
        return form

    def form_valid(self, form):
        if form.is_valid():
            md = list(form.cleaned_data["mensajeriadistritosl"].values_list(
                "pk", flat=True
            ))
            form.instance.mensajeriadistritos = None if len(md) == 0 else md
        return super(AreaEditar, self).form_valid(form)


class AreaActivar(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/area/activar.html"
    model = Area
    form_class = FormAreaActivar

    def get_context_data(self, **kwargs):
        context = super(AreaActivar, self).get_context_data(**kwargs)
        context["botonguardartexto"] = "Inactivar" if self.get_object().activo else "Activar"
        return context

    def form_valid(self, form, ):
        if form.is_valid():
            form.instance.activo = not form.instance.activo
        return super(AreaActivar, self).form_valid(form)


class AreaEliminar(TemplateValidaLogin, VistaEliminacion):
    template_name = "organizacion/area/eliminar.html"
    model = Area


class AreaMover(TemplateValidaLogin, VistaEdicion):
    template_name = "organizacion/area/mover.html"
    content_type = "application/json"
    model = Area
    form_class = FormAreaMover

    def form_valid(self, form, ):
        self.object = self.get_object()
        success = False
        if form.is_valid():
            cldt = form.cleaned_data
            pos = cldt["aposicion"]
            padre = cldt["apadre"]
            areaActual = self.object
            padreActual = areaActual.padre
            ordenActual = areaActual.orden
            if (not padreActual and not padre) or (padreActual and padreActual.pk == padre):
                oMin = min(pos, ordenActual)
                oMax = max(pos, ordenActual)
                orientacion = 1 if ordenActual == oMax else -1
                if orientacion == 1:
                    oMin += 1
                    pos += 1
                if not padreActual:
                    Area.objects.filter(padre=None).filter(
                        orden__range=[oMin, oMax]
                    ).exclude(pk=areaActual.pk).update(orden=F("orden") + orientacion)
                else:
                    padreActual.hijos.filter(
                        orden__range=[oMin, oMax]
                    ).exclude(pk=areaActual.pk).update(orden=F("orden") + orientacion)
                areaActual.orden = pos
                areaActual.save()
            else:
                if not padreActual:
                    Area.objects.filter(
                        orden__gt=ordenActual
                    ).exclude(pk=areaActual.pk).update(orden=F("orden") - 1)
                else:
                    padreActual.subareas.filter(
                        orden__gt=ordenActual
                    ).exclude(pk=areaActual.pk).update(orden=F("orden") - 1)
                if padre > 0:
                    padre = Area.objects.get(pk=padre)
                    newpos = padre.subareas.order_by("-orden").first()
                    areaActual.padre = padre
                else:
                    newpos = Area.objects.filter(padre=None).order_by("-orden").first()
                    areaActual.padre = None
                areaActual.orden = (0 if not newpos else newpos.orden) + 1
                areaActual.save()
            success = True
        return self.render_to_response(self.get_context_data(form=form, success=success))


class AreaDetalle(TemplateValidaLogin, DetailView):
    template_name = "organizacion/area/detalle.html"
    model = Area
    http_method_names = "post"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        context["oArea"] = self.object
        return self.render_to_response(context=context)
