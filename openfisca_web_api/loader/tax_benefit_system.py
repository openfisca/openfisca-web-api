# -*- coding: utf-8 -*-

import importlib


def build_tax_benefit_system(country_package_name):
    try:
        country_package = importlib.import_module(country_package_name)
    except ImportError:
        raise ValueError(
            u"{} is not installed in your current environment".format(country_package_name).encode('utf-8'))
    return country_package.CountryTaxBenefitSystem()


def build_headers(tax_benefit_system):
    package_name, version = tax_benefit_system.get_package_metadata()
    return {
        'Country-Package': package_name,
        'Country-Package-Version': version
        }
