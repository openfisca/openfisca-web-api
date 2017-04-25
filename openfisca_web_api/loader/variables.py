# -*- coding: utf-8 -*-

import datetime
import inspect
import textwrap


def format_value(value):
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def build_source_url(country_package_metadata, source_file_path, start_line_number, source_code):
    nb_lines = source_code.count('\n')
    return '{}/blob/{}{}#L{}-L{}'.format(
        country_package_metadata['repository_url'],
        country_package_metadata['version'],
        source_file_path,
        start_line_number,
        start_line_number + nb_lines - 1,
        ).encode('utf-8')


def build_formulas(variable, country_package_metadata):
    source_code, start_line_number = inspect.getsourcelines(variable.formula_class.function)
    source_code = textwrap.dedent(''.join(source_code))
    return {
        '0001-01-01': {
            'source': build_source_url(
                country_package_metadata,
                variable.formula_class.source_file_path,
                start_line_number,
                source_code
                ),
            'content': source_code,
            }
        }


def build_variable(variable, country_package_metadata):
    result = {
        'description': variable.label,
        'valueType': variable.__class__.__name__.strip('Col'),
        'defaultValue': format_value(variable.default),
        'definitionPeriod': variable.definition_period,
        'entity': variable.entity.key,
        'source': build_source_url(
            country_package_metadata,
            variable.formula_class.source_file_path,
            variable.formula_class.start_line_number,
            variable.formula_class.source_code
            ),
        }

    if variable.url:
        result['references'] = variable.url
    if hasattr(variable.formula_class, 'function') and variable.formula_class.function:
        result['formulas'] = build_formulas(variable, country_package_metadata)

    return result


def build_variables(tax_benefit_system, country_package_metadata):
    return {
        name: build_variable(variable, country_package_metadata)
        for name, variable in tax_benefit_system.column_by_name.iteritems()
        }
