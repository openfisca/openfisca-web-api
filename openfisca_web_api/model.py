# -*- coding: utf-8 -*-


import os

from openfisca_core import decompositions, reforms


# Declarations, initialized in environment module

build_reform_function_by_key = None
decomposition_json_by_file_path_cache = {}
input_variables_and_parameters_by_column_name_cache = {}
input_variables_extractor = None
parameters_json_cache = None
reform_by_full_key = None
tax_benefit_system = None
TaxBenefitSystem = None


def get_cached_composed_reform(reform_keys, tax_benefit_system):
    if reform_by_full_key is None:
        raise Exception('Cannot use reforms when none has been loaded in the instance configuration')\

    full_key = '.'.join(
        [tax_benefit_system.full_key] + reform_keys
        if isinstance(tax_benefit_system, reforms.AbstractReform)
        else reform_keys
        )
    composed_reform = reform_by_full_key.get(full_key)
    if composed_reform is None:
        build_reform_functions = [build_reform_function_by_key[reform_key] for reform_key in reform_keys]
        composed_reform = reforms.compose_reforms(
            build_functions_and_keys = zip(build_reform_functions, reform_keys),
            tax_benefit_system = tax_benefit_system,
            )
        assert full_key == composed_reform.full_key
        reform_by_full_key[full_key] = composed_reform
    return composed_reform


def get_cached_or_new_decomposition_json(tax_benefit_system, xml_file_name = None):
    if xml_file_name is None:
        xml_file_name = tax_benefit_system.DEFAULT_DECOMP_FILE
    global decomposition_json_by_file_path_cache
    decomposition_json = decomposition_json_by_file_path_cache.get(xml_file_name)
    if decomposition_json is None:
        xml_file_path = os.path.join(tax_benefit_system.DECOMP_DIR, xml_file_name)
        decomposition_json = decompositions.get_decomposition_json(tax_benefit_system, xml_file_path)
        decomposition_json_by_file_path_cache[xml_file_name] = decomposition_json
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
