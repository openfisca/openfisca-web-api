# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


import datetime
import importlib
import json
import logging
import os
import sys
import weakref
import xml.etree

from biryani import strings
from openfisca_core import decompositionsxml, periods

import openfisca_web_api
from . import conv, model


app_dir = os.path.dirname(os.path.abspath(__file__))


class ValueAndError(list):  # Can't be a tuple subclass, because WeakValueDictionary doesn't work with (sub)tuples.
    pass


def load_environment(global_conf, app_conf):
    """Configure the application environment."""
    conf = openfisca_web_api.conf  # Empty dictionary
    conf.update(strings.deep_decode(global_conf))
    conf.update(strings.deep_decode(app_conf))
    conf.update(conv.check(conv.struct(
        {
            'app_conf': conv.set_value(app_conf),
            'app_dir': conv.set_value(app_dir),
            'cache_dir': conv.default(os.path.join(os.path.dirname(app_dir), 'cache')),
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
            'reforms': conv.pipe(
                conv.ini_items_list_to_ordered_dict,
                conv.uniform_mapping(
                    conv.noop,
                    conv.module_function_str_to_function,
                    ),
                ),
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

    class TaxBenefitSystem(CountryTaxBenefitSystem):
        decomposition_json_by_filename_cache = None
        instance_and_error_couple_by_json_str_cache = {}  # class attribute

        class Scenario(CountryTaxBenefitSystem.Scenario):
            instance_and_error_couple_by_json_str_cache = weakref.WeakValueDictionary()  # class attribute

            @classmethod
            def cached_or_new(cls):
                return conv.check(cls.json_to_cached_or_new_instance)(None)

            @classmethod
            def make_json_to_cached_or_new_instance(cls, cache_dir, repair, tax_benefit_system):
                def json_to_cached_or_new_instance(value, state = None):
                    json_str = json.dumps(value, separators = (',', ':')) if value is not None else None
                    instance_and_error_couple = cls.instance_and_error_couple_by_json_str_cache.get(json_str)
                    if instance_and_error_couple is None:
                        instance_and_error_couple = cls.make_json_to_instance(cache_dir, repair, tax_benefit_system)(
                            value, state = state or conv.default_state)
                        # Note: Call to ValueAndError() is needed below, otherwise it raises TypeError: cannot create
                        # weak reference to 'tuple' object.
                        cls.instance_and_error_couple_by_json_str_cache[json_str] = ValueAndError(
                            instance_and_error_couple)
                    return instance_and_error_couple

                return json_to_cached_or_new_instance

        def __init__(self):
            super(TaxBenefitSystem, self).__init__()
            self.decomposition_json_by_filename_cache = {}

        @classmethod
        def cached_or_new(cls):
            return conv.check(cls.json_to_cached_or_new_instance)(None)

        def get_decomposition_json(self, xml_filename):
            decomposition_json = self.decomposition_json_by_filename_cache.get(xml_filename)
            if decomposition_json is None:
                xml_file_path = os.path.join(self.DECOMP_DIR, xml_filename)
                decomposition_tree = xml.etree.ElementTree.parse(xml_file_path)
                decomposition_xml_json = conv.check(decompositionsxml.xml_decomposition_to_json)(
                    decomposition_tree.getroot())
                decomposition_xml_json = conv.check(decompositionsxml.make_validate_node_xml_json(self))(
                    decomposition_xml_json)
                decomposition_json = decompositionsxml.transform_node_xml_json_to_json(decomposition_xml_json)
                self.decomposition_json_by_filename_cache[xml_filename] = decomposition_json
            return decomposition_json

        @classmethod
        def json_to_cached_or_new_instance(cls, value, state = None):
            json_str = json.dumps(value, separators = (',', ':')) if value is not None else None
            instance_and_error_couple = cls.instance_and_error_couple_by_json_str_cache.get(json_str)
            if instance_and_error_couple is None:
                instance_and_error_couple = cls.json_to_instance(value, state = state or conv.default_state)
                # Note: Call to ValueAndError() is needed below, otherwise it raises TypeError: cannot create weak
                # reference to 'tuple' object.
                cls.instance_and_error_couple_by_json_str_cache[json_str] = ValueAndError(instance_and_error_couple)
            return instance_and_error_couple

    model.TaxBenefitSystem = TaxBenefitSystem
    model.tax_benefit_system = tax_benefit_system = TaxBenefitSystem.cached_or_new()

    tax_benefit_system.prefill_cache()

    # Cache default decomposition.
    tax_benefit_system.get_decomposition_json(tax_benefit_system.DEFAULT_DECOMP_FILE)

    # Compute and cache compact legislation for each first day of month since at least 2 legal years.
    today = periods.instant(datetime.date.today())
    first_day_of_year = today.offset('first-of', 'year')
    instant = first_day_of_year.offset(-2, 'year')
    two_years_later = first_day_of_year.offset(2, 'year')
    while instant < two_years_later:
        tax_benefit_system.get_compact_legislation(instant)
        instant = instant.offset(1, 'month')
