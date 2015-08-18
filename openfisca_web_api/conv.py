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


"""Conversion functions"""


import collections

from openfisca_core.conv import *  # noqa

from . import conf


def N_(message):
    return message


# Level 1 converters


ini_items_list_to_ordered_dict = pipe(
    cleanup_line,
    function(lambda value: value.split('\n')),
    uniform_sequence(
        pipe(
            cleanup_line,
            function(lambda value: value.split('=')),
            uniform_sequence(cleanup_line),
            ),
        ),
    test(
        lambda values: len(list(set(value[0] for value in values))) == len(values),
        error = N_(u'Key duplicates found in items list'),
        ),
    function(collections.OrderedDict),
    )


def jsonify_value(value):
    if isinstance(value, dict):
        return collections.OrderedDict(
            (unicode(item_key), jsonify_value(item_value))
            for item_key, item_value in value.iteritems()
            )
    if isinstance(value, list):
        return [
            jsonify_value(item)
            for item in value
            ]
    return value


# Defer converter creation for conf to load.
def make_str_to_reforms():
    return pipe(
        test_isinstance(list),
        uniform_sequence(
            pipe(
                test_isinstance(basestring),
                empty_to_none,
                test_in((conf['reforms'] or {}).keys()),
                ),
            drop_none_items = True,
            ),
        empty_to_none,
        )


def module_and_function_names_to_function(values, state = None):
    import importlib
    if values is None:
        return values, None
    module_name, function_name = values
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        return values, unicode(exc)
    function = getattr(module, function_name, None)
    if state is None:
        state = default_state
    if function is None:
        return values, state._(u'Function "{}" not found in module "{}"'.format(function_name, module))
    return function, None


str_to_module_and_function_names = function(lambda value: value.rsplit('.', 1))


def make_validate_variable(reforms, base_tax_benefit_system, reform_tax_benefit_system):
    def validate_variable(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = default_state
        if reforms is None:
            return test_in(
                base_tax_benefit_system.column_by_name,
                error = u'Variable "{}" is unknown in base tax and benefit system'.format(value),
                )(value)
        else:
            is_valid = value in base_tax_benefit_system.column_by_name and \
                value in reform_tax_benefit_system.column_by_name
            return value, None if is_valid else \
                u'Variable "{}" must exist in both base and reform tax and benefit system'.format(value)
    return validate_variable


# Level 2 converters

module_function_str_to_function = pipe(
    str_to_module_and_function_names,
    module_and_function_names_to_function,
    )
