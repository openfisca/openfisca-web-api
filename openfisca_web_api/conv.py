# -*- coding: utf-8 -*-


"""Conversion functions"""


import collections

from openfisca_core.conv import *  # noqa


def N_(message):
    return message


# Level 1 converters


ini_str_to_list = pipe(
    cleanup_line,
    function(lambda value: value.split('\n')),
    uniform_sequence(
        cleanup_line,
        ),
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


def make_str_list_to_reforms():
    # Defer converter creation for model to load.
    from . import model

    def str_list_to_reforms(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = default_state
        value, error = pipe(
            empty_to_none,
            test_isinstance(list),
            )(value)
        if value is None or error is not None:
            return value, error
        if value and model.reforms is None:
            return value, state._(u'No reform was declared to the API')
        declared_reforms_key = model.reforms.keys()
        return uniform_sequence(
            pipe(
                test_isinstance(basestring),
                empty_to_none,
                test_in(declared_reforms_key),
                ),
            drop_none_items = True,
            )(value)
    return str_list_to_reforms


def module_and_function_names_to_function(values, state = None):
    import importlib
    if values is None:
        return values, None
    if state is None:
        state = default_state
    module_name, function_name = values
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return values, {0: state._(u'Module "{}" not found'.format(module_name))}
    function = getattr(module, function_name, None)
    if function is None:
        return values, {1: state._(u'Function "{}" not found in module "{}"'.format(function_name, module))}
    return function, None


str_to_module_and_function_names = function(lambda value: value.rsplit('.', 1))


def make_validate_variable(reforms, base_tax_benefit_system, reform_tax_benefit_system):
    def validate_variable(value, state = None):
        if value is None:
            return value, None
        if state is None:
            state = default_state
        if reforms is None:
            return value, None
        else:
            is_valid = value in base_tax_benefit_system.column_by_name and \
                value in reform_tax_benefit_system.column_by_name
            return value, None if is_valid else \
                u'Variable "{}" must exist in both base and reform tax and benefit system'.format(value)
    return validate_variable


# Level 2 converters

module_and_function_str_to_function = pipe(
    str_to_module_and_function_names,
    module_and_function_names_to_function,
    )
