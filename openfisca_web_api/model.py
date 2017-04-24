# -*- coding: utf-8 -*-

import datetime
import importlib

DATE_FORMAT = "%Y-%m-%d"


def build_values(values):
    result = {}
    stop_date = values[0].get('stop')
    if stop_date:
        result[get_next_day(stop_date)] = None
    for value_object in values:
        result[value_object['start']] = value_object['value']

    return result


def get_next_day(date):
    parsed_date = datetime.datetime.strptime(date, DATE_FORMAT)
    next_day = parsed_date + datetime.timedelta(days=1)
    return next_day.strftime(DATE_FORMAT)


def get_value(date, values):
    candidates = sorted([
        (start_date, value)
        for start_date, value in values.iteritems()
        if start_date <= date  # dates are lexicographically ordered and can be sorted
        ], reverse = True)

    if candidates:
        return candidates[0][1]
    else:
        return None


def build_brackets(brackets):
    result = {}
    # preprocess brackets
    brackets = [{
        'thresholds': build_values(bracket['threshold']),
        'rates': build_values(bracket['rate']),
        } for bracket in brackets]

    dates = set(sum(
        [bracket['thresholds'].keys() + bracket['rates'].keys() for bracket in brackets],
        []))  # flatten the dates and remove duplicates

    # We iterate on all dates as we need to build the whole scale for each of them
    for date in dates:
        for bracket in brackets:
            threshold_value = get_value(date, bracket['thresholds'])
            if threshold_value is not None:
                rate_value = get_value(date, bracket['rates'])
                result[date] = result.get(date) or {}
                result[date][threshold_value] = rate_value

    # Handle stopped parameters: a parameter is stopped if its first bracket is stopped
    latest_date_first_threshold = max(brackets[0]['thresholds'].keys())
    latest_value_first_threshold = brackets[0]['thresholds'][latest_date_first_threshold]
    if latest_value_first_threshold is None:
        result[latest_date_first_threshold] = None

    return result


def build_parameter(parameter_json, parameter_path):
    result = {
        'description': parameter_json.get('description'),
        'id': parameter_path,
        }
    if parameter_json.get('values'):
        result['values'] = build_values(parameter_json['values'])
    elif parameter_json.get('brackets'):
        result['brackets'] = build_brackets(parameter_json['brackets'])
    return result


def walk_legislation_json(node_json, parameters_json, path_fragments):
    children_json = node_json.get('children') or None
    if children_json is None:
        parameter = build_parameter(node_json, u'.'.join(path_fragments))
        parameters_json.append(parameter)
    else:
        for child_name, child_json in children_json.iteritems():
            walk_legislation_json(
                child_json,
                parameters_json = parameters_json,
                path_fragments = path_fragments + [child_name],
                )


def build_tax_benefit_system(country_package_name):
    try:
        country_package = importlib.import_module(country_package_name)
    except ImportError:
        raise ValueError(
            u"{} is not installed in your current environment".format(country_package_name).encode('utf-8'))
    return country_package.CountryTaxBenefitSystem()


def build_parameters(tax_benefit_system):
    legislation_json = tax_benefit_system.get_legislation()
    parameters_json = []
    walk_legislation_json(
        legislation_json,
        parameters_json = parameters_json,
        path_fragments = [],
        )

    return {parameter['id']: parameter for parameter in parameters_json}


def format_value(value):
    if not isinstance(value, datetime.date):
        return value
    else:
        return value.strftime(DATE_FORMAT)


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


def build_headers(tax_benefit_system):
    package_name, version = tax_benefit_system.get_package_metadata()
    return {
        'Country-Package': package_name,
        'Country-Package-Version': version
        }
