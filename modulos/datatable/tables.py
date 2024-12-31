"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals
import copy
from collections import OrderedDict
from hashlib import md5

from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe

from modulos.datatable.columns import Column, BoundColumn, SequenceColumn
from modulos.datatable.columns.basecolumn import ColumnCheckSelect
from modulos.datatable.forms import TipoDocForm
from modulos.datatable.widgets import SearchBox, InfoLabel, Pagination, LengthMenu


class BaseTable(object):

    def __init__(self, data=None):
        self.data = TableData(data, self)
        # Make a copy so that modifying this will not touch the class definition.
        self.columns = copy.deepcopy(self.base_columns)
        # Build table add-ons
        self.addons = TableWidgets(self)

    @property
    def rows(self):
        rows = []
        for obj in self.data:
            # Binding object to each column of each row, so that
            # data structure for each row is organized like this:
            # { boundcol0: td, boundcol1: td, boundcol2: td }
            row = OrderedDict()
            columns = [BoundColumn(obj, col) for col in self.columns if col.space]
            for col in columns:
                row[col] = col.html
            rows.append(row)
        return rows

    @property
    def header_rows(self):
        """
        [ [header1], [header3, header4] ]
        """
        # TO BE FIX: refactor
        header_rows = []
        headers = [col.header for col in self.columns]
        for header in headers:
            if len(header_rows) <= header.row_order:
                header_rows.append([])
            header_rows[header.row_order].append(header)
        return header_rows


class TableData(object):
    def __init__(self, data, table):
        model = getattr(table.opts, "model", None)
        if (data is not None and not hasattr(data, "__iter__") or
                data is None and model is None):
            raise ValueError("Model option or QuerySet-like object data"
                             "is required.")
        if data is None:
            self.queryset = model.objects.all()
        elif isinstance(data, QuerySet):
            self.queryset = data
        else:
            self.list = list(data)

    @property
    def data(self):
        return self.queryset if hasattr(self, "queryset") else self.list

    def __len__(self):
        return (self.queryset.count() if hasattr(self, 'queryset')
                else len(self.list))

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.data[key]


class TableDataMap(object):
    """
    A data map that represents relationship between Table instance and
    Model.
    """
    map = {}

    @classmethod
    def register(cls, token, model, columns):
        if token not in TableDataMap.map:
            TableDataMap.map[token] = (model, columns)

    @classmethod
    def get_model(cls, token):
        return TableDataMap.map.get(token)[0]

    @classmethod
    def get_columns(cls, token):
        return TableDataMap.map.get(token)[1]


class TableWidgets(object):
    def __init__(self, table):
        opts = table.opts
        self.filter_date = opts.filter_date
        self.filter_tipodoc = opts.filter_tipodoc
        self.has_buttons = False
        if opts.toolbar:
            if len(opts.toolbar) > 0:
                self.has_buttons = True
        self.search_box = SearchBox(opts.search, opts.search_placeholder, opts.filter_date)
        self.length_menu = LengthMenu(opts.length_menu)
        self.info_label = InfoLabel(opts.info, opts.info_format)
        self.pagination = Pagination(
            opts.pagination,
            opts.page_length,
            opts.pagination_first,
            opts.pagination_last,
            opts.pagination_prev,
            opts.pagination_next
        )

    def render_dom(self):
        if self.search_box.visible or self.filter_date or self.has_buttons:
            dom = "<'row align-items-center'"
        else:
            dom = ""
        if self.search_box.visible:
            if self.filter_date:
                if self.filter_tipodoc:
                    dom += "<'col-12 col-lg-3 mb-2 mb-lg-0'B><'filter-tipodoc col-12 col-lg-3 mb-2 mb-lg-0'>"
                else:
                    dom += "<'col-12 col-lg-6 mb-2 mb-lg-0'B>"
                dom += "<'filter-date col-12 col-sm-6 col-lg-3 mb-2 mb-md-0'>"
                dom = (dom + "%s") % self.search_box.dom
            else:
                if self.filter_tipodoc:
                    dom += "<'col-12 col-lg-4 mb-2 mb-lg-0'B><'filter-tipodoc col-12 col-lg-4 mb-2 mb-lg-0'>"
                else:
                    dom += "<'col-12 col-lg-8 mb-2 mb-lg-0'B>"
                dom = (dom + "%s") % self.search_box.dom
        else:
            if self.filter_date:
                dom += "<'col-12 col-lg-8 mb-2'B>"
                dom += "<'filter-date col-12 col-lg-4'>"
            elif self.has_buttons:
                dom += "<'col-12 mb-2'B>"
        if self.search_box.visible or self.filter_date or self.has_buttons:
            dom += ">"
        dom += "rt"
        if self.info_label.visible or self.pagination.visible or self.length_menu.visible:
            dom += "<'row pt-2'" + ''.join([self.info_label.dom, self.length_menu.dom, self.pagination.dom]) + ">"
        return mark_safe(dom)


class TableOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)

        # ajax option
        self.ajax = getattr(options, 'ajax', True)
        self.ajax_source = getattr(options, 'ajax_source', None)

        # id attribute of <table> tag
        self.id = getattr(options, 'id', None)

        # build attributes for <table> tag, use bootstrap
        # css class "table table-boarded" as default style
        clsReorder = ""  # " table-row-reorder "  else " "
        attrs = getattr(options, 'attrs', {})
        attrs['class'] = 'dt-bootstrap4 table table-bordered table-hover table-striped table-sm ' + \
                         'dataTable dtr-inline w-100' + \
                         attrs.get('class', '')
        self.attrs = mark_safe(' '.join(['%s="%s"' % (attr_name, attr)
                                         for attr_name, attr in attrs.items()]))
        # build attributes for <thead> and <tbody>
        thead_attrs = getattr(options, 'thead_attrs', {})
        self.thead_attrs = mark_safe(' '.join(['%s="%s"' % (attr_name, attr)
                                               for attr_name, attr in thead_attrs.items()]))
        tbody_attrs = getattr(options, 'tbody_attrs', {})
        self.tbody_attrs = mark_safe(' '.join(['%s="%s"' % (attr_name, attr)
                                               for attr_name, attr in tbody_attrs.items()]))

        # scrolling option
        self.scrollable = getattr(options, 'scrollable', False)
        self.scrolly = getattr(options, 'scrolly', "200")
        self.fixed_columns = getattr(options, 'fixed_columns', None)
        self.fixed_columns_width = getattr(options, 'fixed_columns_width', None)

        # inspect sorting option
        self.sort = []
        for column, order in getattr(options, 'sort', []):
            if not isinstance(column, int):
                raise ValueError('Sorting option must be organized by following'
                                 ' forms: [(0, "asc"), (1, "desc")]')
            if order not in ('asc', 'desc'):
                raise ValueError('Order value must be "asc" or "desc", '
                                 '"%s" is unsupported.' % order)
            self.sort.append((column, order))

        # options for table add-on
        self.processing = getattr(options, 'processing', "Cargando")
        self.search = getattr(options, 'search', True)
        self.search_placeholder = getattr(options, 'search_placeholder', None)

        self.info = getattr(options, 'info', True)
        self.info_format = getattr(options, 'info_format', None)

        self.pagination = getattr(options, 'pagination', True)
        self.page_length = getattr(options, 'page_length', 10)
        self.pagination_first = getattr(options, 'pagination_first', None)
        self.pagination_last = getattr(options, 'pagination_last', None)
        self.pagination_prev = getattr(options, 'pagination_prev', None)
        self.pagination_next = getattr(options, 'pagination_next', None)

        self.length_menu = getattr(options, 'length_menu', True)

        self.zero_records = getattr(options, 'zero_records', 'Ningún registro')
        self.template_name = getattr(options, 'template_name', None)
        # Toolbar
        # id
        # icono
        # texto
        # url
        # modal
        self.rowreorder = getattr(options, 'rowreorder', False)
        self.toolbar = getattr(options, 'toolbar', None)
        self.selectrowcheckbox = getattr(options, 'selectrowcheckbox', False)
        self.filter_date = getattr(options, 'filter_date', False)
        self.filter_tipodoc = getattr(options, 'filter_tipodoc', False)
        if self.filter_tipodoc:
            self.filter_tipodocform = TipoDocForm(tableid=self.id)


class TableMetaClass(type):
    """ Meta class for create Table class instance.
    """

    def __new__(cls, name, bases, attrs):
        opts = TableOptions(attrs.get('Meta', None))
        # take class name in lower case as table's id
        if opts.id is None:
            opts.id = name.lower()
        attrs['opts'] = opts

        # extract declared columns
        columns = []
        for attr_name, attr in attrs.items():
            if isinstance(attr, SequenceColumn):
                columns.extend(attr)
            elif isinstance(attr, Column):
                columns.append(attr)
        columns.sort(key=lambda x: x.instance_order)

        # If this class is subclassing other tables, add their fields as
        # well. Note that we loop over the bases in reverse - this is
        # necessary to preserve the correct order of columns.
        parent_columns = []
        for base in bases[::-1]:
            if hasattr(base, "base_columns"):
                parent_columns = base.base_columns + parent_columns
        base_columns = parent_columns + columns

        # For ajax data source, store columns into global hash map with
        # unique token key. So that, columns can be get to construct data
        # on views layer.
        token = md5(name.encode('utf-8')).hexdigest()
        bcn = copy.deepcopy(base_columns)
        if opts.ajax:
            if opts.selectrowcheckbox:
                checkColumn = ColumnCheckSelect(
                    field="pk",
                    header="",
                    sortable=False,
                    searchable=False,
                    attrs={"class": "w-20px"}
                )
                bcn = [checkColumn] + bcn
            TableDataMap.register(token, opts.model, bcn)

        attrs["columns"] = bcn
        attrs['token'] = token
        attrs['base_columns'] = bcn

        return super(TableMetaClass, cls).__new__(cls, name, bases, attrs)


Table = TableMetaClass(str('Table'), (BaseTable,), {})
