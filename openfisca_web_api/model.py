# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import xml.etree

from openfisca_core import decompositionsxml, reforms

from . import conv


# Declarations, initialized in environment module

build_reform_function_by_key = None
decomposition_json_by_file_path_cache = {}
input_variables_and_parameters_by_column_name_cache = {}
input_variables_extractor = None
parameters_file_path = None
parameters_json_cache = None
reform_by_full_key = None
tax_benefit_system = None
TaxBenefitSystem = None


def get_cached_composed_reform(reform_keys, tax_benefit_system):
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
        decomposition_tree = xml.etree.ElementTree.parse(xml_file_path)
        decomposition_xml_json = conv.check(decompositionsxml.xml_decomposition_to_json)(
            decomposition_tree.getroot())
        decomposition_xml_json = conv.check(decompositionsxml.make_validate_node_xml_json(tax_benefit_system))(
            decomposition_xml_json)
        decomposition_json = decompositionsxml.transform_node_xml_json_to_json(decomposition_xml_json)
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
