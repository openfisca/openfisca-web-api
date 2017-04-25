# -*- coding: utf-8 -*-

from .tax_benefit_system import build_tax_benefit_system, build_headers
from .parameters import build_parameters
from .variables import build_variables


def extract_description(items):
    return {
        name: {'description': item['description']}
        for name, item in items.iteritems()
        }


def build_data(country_package_name):
    tax_benefit_system = build_tax_benefit_system(country_package_name)
    parameters = build_parameters(tax_benefit_system)
    variables = build_variables(tax_benefit_system)
    return {
        'tax_benefit_system': tax_benefit_system,
        'headers': build_headers(tax_benefit_system),
        'parameters': parameters,
        'parameters_description': extract_description(parameters),
        'variables': variables,
        'variables_description': extract_description(variables),
        }
