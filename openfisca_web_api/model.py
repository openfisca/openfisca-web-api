# -*- coding: utf-8 -*-

import datetime
import importlib

DATE_FORMAT = "%Y-%m-%d"

def get_next_day(date):
    parsed_date = datetime.datetime.strptime(date, DATE_FORMAT)
    next_day = parsed_date + datetime.timedelta(days=1)
    return next_day.strftime(DATE_FORMAT)


def build_parameter(parameter_json, parameter_path):
    result = {}
    result['description'] = parameter_json.get('description')
    result['id'] = parameter_path
    result['values'] = {}
    if parameter_json.get('values'):  # we don't handle baremes yet
        values = parameter_json.get('values')
        stop_date = values[0].get('stop')
        if stop_date:
            result['values'][get_next_day(stop_date)] = None
        for value_object in values:
            result['values'][value_object['start']] = value_object['value']
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


def build_parameters(country_package_name):
    country_package = importlib.import_module(country_package_name)
    tax_benefit_system = country_package.CountryTaxBenefitSystem()
    legislation_json = tax_benefit_system.get_legislation()
    parameters_json = []
    walk_legislation_json(
        legislation_json,
        parameters_json = parameters_json,
        path_fragments = [],
        )

    return {parameter['id']: parameter for parameter in parameters_json}
