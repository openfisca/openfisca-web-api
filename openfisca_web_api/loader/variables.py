# -*- coding: utf-8 -*-

import datetime

from commons import DATE_FORMAT


def format_value(value):
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def build_source_url(country_package_metadata, source_file_path, start_line_number, source_code):
    return '{}/blob/{}{}'.format(
        country_package_metadata['repository_url'],
        country_package_metadata['version'],
        source_file_path,
        ).encode('utf-8')

def build_variables(tax_benefit_system, country_package_metadata):
    return {
        name: {
            'description': variable.label,
            'valueType': variable.__class__.__name__.strip('Col'),
            'defaultValue': format_value(variable.default),
            'definitionPeriod': variable.definition_period,
            'entity': variable.entity.key,
            # 'reference': '',
            'source': build_source_url(
                country_package_metadata,
                variable.formula_class.source_file_path,
                variable.formula_class.start_line_number,
                variable.formula_class.source_code
                )
            }
        for name, variable in tax_benefit_system.column_by_name.iteritems()
        }
