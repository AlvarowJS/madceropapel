"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django_select2.forms import ModelSelect2Widget, ModelSelect2MultipleWidget, HeavySelect2Widget


class MADModelSelect2Widget(ModelSelect2Widget):
    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        fqs = super(MADModelSelect2Widget, self).filter_queryset(request, term, queryset, **dependent_fields)
        sel_id = request.GET.get("sel_id", None)
        if sel_id:
            fqs = fqs.filter(pk=int(sel_id))
        return fqs


class MADModelSelect2MultipleWidget(ModelSelect2MultipleWidget):
    pass


class SGDModelSelect2Widget(HeavySelect2Widget):
    pass


class MADNucleoModelSelect2Widget(HeavySelect2Widget):
    pass
