# -*- coding: utf-8 -*-

from openfisca_dummy_country import CountryTaxBenefitSystem

def build_parameter(parameter_json, parameter_path):
    result = {}
    result['description'] = parameter_json.get('description')
    result['id'] = parameter_path
    result['values'] = {}
    if parameter_json.get('values'):
        for value_object in parameter_json['values']:
            result['values'][value_object['start']] = value_object['value']
    else:
        # Handle baremes here
        pass
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


def build_parameters():
    tax_benefit_system = CountryTaxBenefitSystem()
    legislation_json = tax_benefit_system.get_legislation()
    parameters_json = []
    walk_legislation_json(
        legislation_json,
        parameters_json = parameters_json,
        path_fragments = [],
        )

    return {parameter['id']: parameter for parameter in parameters_json}


