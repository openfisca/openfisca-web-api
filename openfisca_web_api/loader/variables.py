# -*- coding: utf-8 -*-

import datetime

from commons import DATE_FORMAT


def format_value(value):
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def build_variables(tax_benefit_system):
    return {
        name: {
            'description': variable.label,
            'valueType': variable.__class__.__name__.strip('Col'),
            'defaultValue': format_value(variable.default),
            'definitionPeriod': variable.definition_period,
            'entity': variable.entity.key,
            # 'reference': '',
            # 'source': '', # TODO : use variable.formula_class.(start_line_number|source_code|source_file_path)
            }
        for name, variable in tax_benefit_system.column_by_name.iteritems()
        }
