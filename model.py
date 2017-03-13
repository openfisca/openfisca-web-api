# -*- coding: utf-8 -*-

from openfisca_france import CountryTaxBenefitSystem

def walk_legislation_json(node_json, parameters_json, path_fragments):
    children_json = node_json.get('children') or None
    if children_json is None:
        parameter_json = dict(node_json.copy())  # No need to deepcopy since it is a leaf.
        parameter_json['description'] = node_json.get('description')
        parameter_json['name'] = u'.'.join(path_fragments)
        parameters_json.append(parameter_json)
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


