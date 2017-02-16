# -*- coding: utf-8 -*-

"""Environment configuration"""

import collections
import datetime
import importlib
import logging
import multiprocessing
import os
import pkg_resources
import sys
import weakref

from biryani import strings
from openfisca_core import periods
try:
    from openfisca_parsers import input_variables_extractors
except ImportError:
    input_variables_extractors = None

from . import conf, conv, model


app_dir = os.path.dirname(os.path.abspath(__file__))

# Initialized in load_environment.
country_package_dir_path = None
country_package_version = None
api_package_version = None
cpu_count = None

log = logging.getLogger(__name__)


class ValueAndError(list):  # Can't be a tuple subclass, because WeakValueDictionary doesn't work with (sub)tuples.
    pass


def get_relative_file_path(absolute_file_path):
    '''
    Example:
    absolute_file_path = "/home/xxx/Dev/openfisca/openfisca-france/openfisca_france/param/param.xml"
    result = "openfisca_france/param/param.xml"
    '''
    global country_package_dir_path
    assert country_package_dir_path is not None
    relative_file_path = absolute_file_path[len(country_package_dir_path):]
    if relative_file_path.startswith('/'):
        relative_file_path = relative_file_path[1:]
    return relative_file_path


def load_environment(global_conf, app_conf):
    """Configure the application environment."""
    conf.update(strings.deep_decode(global_conf))
    conf.update(strings.deep_decode(app_conf))
    conf.update(conv.check(conv.struct(
        {
            'app_conf': conv.set_value(app_conf),
            'app_dir': conv.set_value(app_dir),
            'country_package': conv.pipe(
                conv.make_input_to_slug(separator = u'_'),
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
            'extensions': conv.ini_str_to_list,
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
        errorware['show_exceptions_in_wsgi_errors'] = conf.get('show_exceptions_in_wsgi_errors', True)

    # Initialize tax-benefit system.
    country_package = importlib.import_module(conf['country_package'])
    tax_benefit_system = country_package.CountryTaxBenefitSystem()

    extensions = conf['extensions']
    if extensions is not None:
        for extension in extensions:
            tax_benefit_system.load_extension(extension)

    class Scenario(tax_benefit_system.Scenario):
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

    tax_benefit_system.Scenario = Scenario

    model.tax_benefit_system = tax_benefit_system

    log.debug(u'Pre-fill tax and benefit system cache.')
    tax_benefit_system.prefill_cache()

    log.debug(u'Initialize reforms.')
    reforms = conv.check(
        conv.uniform_sequence(
            conv.module_and_function_str_to_function,
            )
        )(conf['reforms'])
    model.reforms = {}
    model.reformed_tbs = {}
    if reforms is not None:
        for reform in reforms:
            reformed_tbs = reform(tax_benefit_system)
            key = reformed_tbs.key
            full_key = reformed_tbs.full_key
            model.reforms[key] = reform
            model.reformed_tbs[full_key] = reformed_tbs

    log.debug(u'Cache default decomposition.')
    if tax_benefit_system.decomposition_file_path is not None:
        # Ignore the returned value, because we just want to pre-compute the cache.
        model.get_cached_or_new_decomposition_json(tax_benefit_system)

    log.debug(u'Initialize lib2to3-based input variables extractor.')
    if input_variables_extractors is not None:
        model.input_variables_extractor = input_variables_extractors.setup(tax_benefit_system)

    global country_package_dir_path
    # - Do not use pkg_resources.get_distribution(conf["country_package"]).location
    #   because it returns a wrong path in virtualenvs (<venv>/lib versus <venv>/local/lib)
    # - Use os.path.abspath because when the web API is runned in development with "paster serve",
    #   __path__[0] == 'openfisca_france' for example. Then, get_relative_file_path won't be able
    #   to find the relative path of an already relative path.
    country_package_dir_path = os.path.abspath(country_package.__path__[0])

    global api_package_version
    api_package_version = pkg_resources.get_distribution('openfisca_web_api').version

    global country_package_version
    country_package_version = pkg_resources.get_distribution(conf["country_package"]).version

    log.debug(u'Cache legislation JSON with references to original XML.')
    legislation_json = tax_benefit_system.get_legislation(with_source_file_infos=True)
    parameters_json = []
    walk_legislation_json(
        legislation_json,
        descriptions = [],
        parameters_json = parameters_json,
        path_fragments = [],
        )
    model.parameters_json_cache = parameters_json

    if not conf['debug']:
        # Do this after tax_benefit_system.get_legislation(with_source_file_infos=True).
        log.debug(u'Compute and cache compact legislation for each first day of month since at least 2 legal years.')
        today = periods.instant(datetime.date.today())
        first_day_of_year = today.offset('first-of', 'year')
        instant = first_day_of_year.offset(-2, 'year')
        two_years_later = first_day_of_year.offset(2, 'year')
        while instant < two_years_later:
            tax_benefit_system.get_compact_legislation(instant)
            instant = instant.offset(1, 'month')

    # Initialize multiprocessing and load_alert
    if conf['load_alert']:
        global cpu_count
        cpu_count = multiprocessing.cpu_count()


def walk_legislation_json(node_json, descriptions, parameters_json, path_fragments):
    children_json = node_json.get('children') or None
    if children_json is None:
        parameter_json = node_json.copy()  # No need to deepcopy since it is a leaf.
        description = u' ; '.join(
            fragment
            for fragment in descriptions + [node_json.get('description')]
            if fragment
            ) or None
        if description is not None:
            parameter_json['description'] = description
        parameter_json['name'] = u'.'.join(path_fragments)
        if 'xml_file_path' in node_json:
            parameter_json['xml_file_path'] = get_relative_file_path(node_json['xml_file_path'])
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
