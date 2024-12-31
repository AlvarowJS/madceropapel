"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.conf import settings
from django.db.models import Case, When, Value, IntegerField, Q
from django.http import JsonResponse
from django.utils import timezone
from django_select2.views import AutoResponseView
from pytz import timezone as pytz_timezone

from apps.organizacion.models import Area


class DocumentoReferenciaDepListar(AutoResponseView):
    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': self.widget.label_from_instance(obj),
                    'id': obj.pk,
                    'depsig': obj.siglas,
                    'direccion': obj.direccion,
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })


class DocumentoDestinoUOListar(AutoResponseView):
    def get_queryset(self):
        qs = self.widget.filter_queryset(
            self.request,
            self.term,
            self.queryset
        )
        dep = self.request.GET.get("dep")
        if str(dep).startswith("0"):
            qs = qs.exclude(rindentepadre__isnull=False)  # .exclude(esrindente=True)
        elif dep:
            qs = qs.filter(rindentepadre_id=int(dep))
        return qs

    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': self.widget.label_from_instance(obj),
                    'id': obj.pk,
                    'depsig': obj.dependencia.siglas if not obj.rindentepadre else obj.rindentepadre.siglas
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })


class DocumentoDestinoPTListar(AutoResponseView):
    def get_queryset(self):
        qs = super(DocumentoDestinoPTListar, self).get_queryset()
        qs = qs.annotate(
            ordencargo=Case(
                When(
                    Q(Q(esjefe=True) | Q(tipo="EN")),
                    then=Value(1)
                ),
                default=Value(2),
                output_field=IntegerField()
            )
        ).order_by("ordencargo", "esjefemodo", "persona__apellidocompleto")
        return qs

    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': self.widget.label_from_instance(obj) +
                            ((" - <strong>%s</strong>" % obj.Cargo()) if obj.ordencargo == 1 else ""),
                    'id': obj.pk,
                    'cargo': obj.Cargo(),
                    'ordencargo': obj.ordencargo,
                    'nombre': self.widget.label_from_instance(obj)
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })


class DocumentoResponsableListar(AutoResponseView):
    def get_queryset(self):
        qs = super(DocumentoResponsableListar, self).get_queryset()
        periodoactual = self.request.user.persona.periodotrabajoactual(self.request.session.get("cambioperiodo"))
        fechaActual = timezone.now().astimezone(pytz_timezone(settings.TIME_ZONE))
        qs = qs.annotate(
            ordencargo=Case(
                When(id=periodoactual.id, then=0),
                default=1
            )
        ).filter(
            Q(tipo="NN")
            |
            Q(
                tipo="EN", inicio__lte=fechaActual, fin__gte=fechaActual,
                encargaturaplantilla__isnull=False,
                encargaturaplantillaanulacion__isnull=True
            )
            |
            Q(
                Q(tipo="EP", inicio__lte=fechaActual, activo=True),
                Q(Q(fin__gte=fechaActual) | Q(fin__isnull=True))
            )
        ).order_by("ordencargo", "-tipo", "persona__apellidocompleto")
        return qs

    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': "%s - %s" % (
                        self.widget.label_from_instance(obj),
                        "encargado" if obj.tipo == "EN" else (
                            "responsable" if not obj.area.paracomisiones else obj.Cargo()
                        )
                    ),
                    'id': obj.pk,
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })


class DocumentoTipoListar(AutoResponseView):
    def get(self, request, *args, **kwargs):
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get('term', request.GET.get('term', ''))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse({
            'results': [
                {
                    'text': "%s" % self.widget.label_from_instance(obj),
                    'tieneforma': obj.documentotipo.tieneforma,
                    'id': obj.pk,
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })
