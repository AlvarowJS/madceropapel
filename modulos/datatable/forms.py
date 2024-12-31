"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

#!/usr/bin/env python
# coding: utf-8
from django import forms


class QueryDataForm(forms.Form):
    """
    Non-interactive form that used to organize query parameters
    of DataTables.
    """
    sEcho = forms.CharField()
    iDisplayStart = forms.IntegerField()
    iDisplayLength = forms.IntegerField()
    iColumns = forms.IntegerField()
    sSearch = forms.CharField(required=False)
    bRegex = forms.BooleanField(required=False)
    iSortingCols = forms.IntegerField(required=False)

    def __init__(self, data=None, *args, **kwargs):
        super(QueryDataForm, self).__init__(data, *args, **kwargs)
        for key in data.keys():
            if key.startswith("iSortCol"):
                self.fields[key] = forms.IntegerField()
            if key.startswith("sSortDir"):
                self.fields[key] = forms.CharField()


class TipoDocForm(forms.Form):
    selector = forms.IntegerField(
        required=False
    )

    def __init__(self, tableid, *args, **kwargs):
        super(TipoDocForm, self).__init__(*args, **kwargs)
        from django_select2.forms import ModelSelect2Widget
        from apps.tramite.models import DocumentoTipo
        self.fields["selector"].widget = ModelSelect2Widget(
            queryset=DocumentoTipo.objects.filter().order_by("nombre"),
            search_fields=["nombre__icontains"],
            max_results=10,
        )
        self.fields["selector"].widget.attrs['data-placeholder'] = 'Tipo de Documento'
        self.fields["selector"].widget.attrs['data-width'] = '100%'
        self.fields["selector"].widget.attrs['id'] = "%s_cbtipodoc" % tableid
