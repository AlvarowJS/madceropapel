"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.db.models.fields.related import ForeignObject
from django.db.models.options import Options
from django.db.models.sql.constants import INNER
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import ExtraWhere


class CustomJoin(Join):
    def __init__(self, subquery, subquery_params, parent_alias, table_alias, join_type, join_field, nullable):
        self.subquery_params = subquery_params
        self.table_alias2 = table_alias
        super(CustomJoin, self).__init__(subquery, parent_alias, table_alias, join_type, join_field, nullable)

    def as_sql(self, compiler, connection):
        params = []
        sql = []
        alias_str = '' if self.table_alias2 == self.table_name else ('%s' % self.table_alias2)
        params.extend(self.subquery_params)
        qn1 = compiler.quote_name_unless_alias
        qn2 = connection.ops.quote_name
        #
        self.join_type = "INNER JOIN"
        sql.append('%s (%s) "%s" ON (' % (self.join_type, self.table_name, alias_str))

        for index, (lhs_col, rhs_col) in enumerate(self.join_cols):
            if index != 0:
                sql.append('AND')
            rhs_pri = "%s.%s" % (
                qn1(self.parent_alias),
                qn2(lhs_col)
            )
            sql.append('%s = %s.%s' % (
                rhs_pri,
                qn1(self.table_alias2),
                qn2(rhs_col)
            ))
        extra_cond = self.join_field.get_extra_restriction(
            compiler.query.where_class, self.table_alias, self.parent_alias
        )
        if extra_cond:
            extra_sql, extra_params = compiler.compile(extra_cond)
            extra_sql = 'AND (%s)' % extra_sql
            params.extend(extra_params)
            sql.append('%s' % extra_sql)
        sql.append(')')
        print("=" * 80)
        print("JOIN:", ' '.join(sql), params)
        print("=" * 80)
        return ' '.join(sql), params


def query_to_queryset(table, query, subquery, alias, on_relateds):
    """
        query: Consulta donde quieres hacer inner join
        subquery: Sub Consulta que quieres añadir al query
        alias: Nombre de la Sub Consulta
        on_relateds: On Filter de ambas query
    """
    foreign_object = ForeignObject(to=subquery, on_delete=[None], from_fields=[None], to_fields=[None], rel=None)
    foreign_object.opts = Options(table._meta)
    foreign_object.opts.model = table
    foreign_object.get_joining_columns = lambda: [
        (rhs_field, lhs_field) for lhs_field, rhs_field in
        on_relateds.items()
    ]
    subquery_sql, subquery_params = subquery.query.sql_with_params()
    joinquery = CustomJoin(
        subquery_sql, subquery_params, table._meta.db_table, alias, INNER, foreign_object, True
    )
    query.query.join(joinquery)
    print(query.query)
    _result = ""
    return _result
