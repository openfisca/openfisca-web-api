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


"""Environment configuration"""


import collections
import datetime
import importlib
import logging
import os
import pkg_resources
import subprocess
import sys
import weakref

from biryani import strings
from openfisca_core import periods, reforms
try:
    from openfisca_parsers import input_variables_extractors
except ImportError:
    input_variables_extractors = None

import openfisca_web_api
from . import conf, conv, model


app_dir = os.path.dirname(os.path.abspath(__file__))
country_package_git_head_sha = None
git_head_sha = None


class ValueAndError(list):  # Can't be a tuple subclass, because WeakValueDictionary doesn't work with (sub)tuples.
    pass


def get_git_head_sha(cwd = os.path.dirname(__file__)):
    output = subprocess.check_output(['git', 'rev-parse', '--verify', 'HEAD'], cwd=cwd)
    return output.rstrip('\n')


def get_parameters_file_path():
    country_package_dir_path = pkg_resources.get_distribution(conf['country_package']).location
    parameters_file_absolute_path = model.tax_benefit_system.legislation_xml_file_path
    parameters_file_path = parameters_file_absolute_path[len(country_package_dir_path):]
    if parameters_file_path.startswith('/'):
        parameters_file_path = parameters_file_path[1:]
    return parameters_file_path


def load_environment(global_conf, app_conf):
    """Configure the application environment."""
    conf = openfisca_web_api.conf  # Empty dictionary
    conf.update(strings.deep_decode(global_conf))
    conf.update(strings.deep_decode(app_conf))
    conf.update(conv.check(conv.struct(
        {
            'app_conf': conv.set_value(app_conf),
            'app_dir': conv.set_value(app_dir),
            'country_package': conv.pipe(
                conv.make_input_to_slug(separator = u'_'),
                conv.test_in((
                    u'openfisca_france',
                    u'openfisca_tunisia',
                    u'openfisca_tunisia_pension',
                    )),
                conv.not_none,
                ),
            'debug': conv.pipe(conv.guess_bool, conv.default(False)),
            'global_conf': conv.set_value(global_conf),
            'i18n_dir': conv.default(os.path.join(app_dir, 'i18n')),
            'load_alert': conv.pipe(conv.guess_bool, conv.default(False)),
            'log_level': conv.pipe(
                conv.default('WARNING'),
                conv.function(lambda log_level: getattr(logging, log_level.upper())),
                ),
            'package_name': conv.default('openfisca-web-api'),
            'realm': conv.default(u'OpenFisca Web API'),
            'reforms': conv.ini_str_to_list,  # Another validation is done below.
            },
        default = 'drop',
        ))(conf))

    # Configure logging.
    logging.basicConfig(level = conf['log_level'], stream = sys.stderr)

    errorware = conf.setdefault('errorware', {})
    errorware['debug'] = conf['debug']
    if not errorware['debug']:
        errorware['error_email'] = conf['email_to']
        errorware['error_log'] = conf.get('error_log', None)
        errorware['error_message'] = conf.get('error_message', 'An internal server error occurred')
        errorware['error_subject_prefix'] = conf.get('error_subject_prefix', 'OpenFisca Web API Error: ')
        errorware['from_address'] = conf['from_address']
        errorware['smtp_server'] = conf.get('smtp_server', 'localhost')

    # Initialize tax-benefit system.

    country_package = importlib.import_module(conf['country_package'])
    CountryTaxBenefitSystem = country_package.init_country()

    class Scenario(CountryTaxBenefitSystem.Scenario):
        instance_and_error_couple_cache = {} if conf['debug'] else weakref.WeakValueDictionary()  # class attribute

        @classmethod
        def make_json_to_cached_or_new_instance(cls, ctx, repair, tax_benefit_system):
            def json_to_cached_or_new_instance(value, state = None):
                key = (unicode(ctx.lang), unicode(value), repair, tax_benefit_system)
                instance_and_error_couple = cls.instance_and_error_couple_cache.get(key)
                if instance_and_error_couple is None:
                    instance_and_error_couple = cls.make_json_to_instance(repair, tax_benefit_system)(
                        value, state = state or conv.default_state)
                    # Note: Call to ValueAndError() is needed below, otherwise it raises TypeError: cannot create
                    # weak reference to 'tuple' object.
                    cls.instance_and_error_couple_cache[key] = ValueAndError(instance_and_error_couple)
                return instance_and_error_couple

            return json_to_cached_or_new_instance

    class TaxBenefitSystem(CountryTaxBenefitSystem):
        pass
    TaxBenefitSystem.Scenario = Scenario

    model.TaxBenefitSystem = TaxBenefitSystem
    model.tax_benefit_system = tax_benefit_system = TaxBenefitSystem()

    tax_benefit_system.prefill_cache()

    # Initialize reforms
    build_reform_functions = conv.check(
        conv.uniform_sequence(
            conv.module_and_function_str_to_function,
            )
        )(conf['reforms'])
    if build_reform_functions is not None:
        api_reforms = [
            build_reform(tax_benefit_system)
            for build_reform in build_reform_functions
            ]
        api_reforms = conv.check(
            conv.uniform_sequence(conv.test_isinstance(reforms.AbstractReform))
            )(api_reforms)
        model.build_reform_function_by_key = {
            reform.key: build_reform
            for build_reform, reform in zip(build_reform_functions, api_reforms)
            }
        model.reform_by_full_key = {
            reform.full_key: reform
            for reform in api_reforms
            }

    # Cache default decomposition.
    model.get_cached_or_new_decomposition_json(tax_benefit_system)

    # Compute and cache compact legislation for each first day of month since at least 2 legal years.
    today = periods.instant(datetime.date.today())
    first_day_of_year = today.offset('first-of', 'year')
    instant = first_day_of_year.offset(-2, 'year')
    two_years_later = first_day_of_year.offset(2, 'year')
    while instant < two_years_later:
        tax_benefit_system.get_compact_legislation(instant)
        instant = instant.offset(1, 'month')

    # Initialize lib2to3-based input variables extractor.
    if input_variables_extractors is not None:
        model.input_variables_extractor = input_variables_extractors.setup(tax_benefit_system)

    # Store Git last commit SHA
    global git_head_sha
    git_head_sha = get_git_head_sha()
    global country_package_git_head_sha
    country_package_git_head_sha = get_git_head_sha(cwd = country_package.__path__[0])

    # Store parameters_file_path cache
    model.parameters_file_path = get_parameters_file_path()

    # Store parameters_json cache
    parameters_json = []
    walk_legislation_json(
        tax_benefit_system.legislation_json,
        descriptions = [],
        parameters_json = parameters_json,
        path_fragments = [],
        )
    model.parameters_json_cache = parameters_json


def walk_legislation_json(node_json, descriptions, parameters_json, path_fragments):
    children_json = node_json.get('children') or None
    if children_json is None:
        parameter_json = node_json.copy()  # No need to deepcopy since it is a leaf.
        description = u' ; '.join(
            fragment
            for fragment in descriptions + [node_json.get('description')]
            if fragment
            )
        parameter_json['description'] = description
        parameter_json['name'] = u'.'.join(path_fragments)
        parameter_json = collections.OrderedDict(sorted(parameter_json.iteritems()))
        parameters_json.append(parameter_json)
    else:
        for child_name, child_json in children_json.iteritems():
            walk_legislation_json(
                child_json,
                descriptions = descriptions + [node_json.get('description')],
                parameters_json = parameters_json,
                path_fragments = path_fragments + [child_name],
                )
