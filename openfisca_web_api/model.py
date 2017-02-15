# -*- coding: utf-8 -*-


from openfisca_core import decompositions
from openfisca_core.reforms import Reform, compose_reforms


# Declarations, initialized in environment module

reforms = None
extensions = None
decomposition_json_by_file_path_cache = {}
input_variables_and_parameters_by_column_name_cache = {}
input_variables_extractor = None
parameters_json_cache = None
reformed_tbs = None
tax_benefit_system = None


def get_cached_composed_reform(reform_keys, tax_benefit_system):
    full_key = '.'.join(
        [tax_benefit_system.full_key] + reform_keys
        if isinstance(tax_benefit_system, Reform)
        else reform_keys
        )
    composed_reform_tbs = reformed_tbs.get(full_key)
    if composed_reform_tbs is None:
        reforms_to_apply = [reforms[reform_key] for reform_key in reform_keys]
        composed_reform_tbs = compose_reforms(reforms_to_apply, tax_benefit_system)
        reformed_tbs[full_key] = composed_reform_tbs
    return composed_reform_tbs


def get_cached_or_new_decomposition_json(tax_benefit_system):
    xml_file_path = tax_benefit_system.decomposition_file_path
    global decomposition_json_by_file_path_cache
    decomposition_json = decomposition_json_by_file_path_cache.get(xml_file_path)
    if decomposition_json is None:
        decomposition_json = decompositions.get_decomposition_json(tax_benefit_system, xml_file_path)
        decomposition_json_by_file_path_cache[xml_file_path] = decomposition_json
    return decomposition_json


def get_cached_input_variables_and_parameters(column):
    """This function uses input_variables_extractor and expects the caller to check it is not None."""
    assert input_variables_extractor is not None
    global input_variables_and_parameters_by_column_name_cache
    input_variables_and_parameters = input_variables_and_parameters_by_column_name_cache.get(column.name)
    if input_variables_and_parameters is None:
        input_variables_and_parameters = input_variables_extractor.get_input_variables_and_parameters(column)
        input_variables_and_parameters_by_column_name_cache[column.name] = input_variables_and_parameters
    return input_variables_and_parameters
