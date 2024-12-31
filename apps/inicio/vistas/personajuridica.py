"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.http import JsonResponse
from django_select2.views import AutoResponseView


class PersonaJuridicaListar(AutoResponseView):
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
                    'ruc': obj.ruc
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })


class PersonaJuridicaRzListar(AutoResponseView):
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
                    'ubigeo': 0 if not obj.ubigeo else obj.ubigeo.id,
                    'direccion': obj.direccion or '',
                    'referencia': obj.referencia or '',
                    'correo': obj.correo or '',
                    'representantetd': obj.representante.tipodocumentoidentidad.id if obj.representante else 0,
                    'representanteid': obj.representante.id if obj.representante else '',
                    'representantenumero': obj.representante.numero if obj.representante else '',
                    'representantecargo': obj.representantecargo or ''
                }
                for obj in context['object_list']
            ],
            'more': context['page_obj'].has_next()
        })
