# -*- coding: utf-8 -*-


from nose.tools import assert_equal, assert_in

from .. import model
from ..controllers.swagger import (
    build_metadata,
    map_path_base_to_swagger,
    map_type_to_swagger,
    map_parameter_to_swagger,
    )
from . import common


def setup_module(module):
    common.get_or_load_app()


def test_metadata_version():
    actual = build_metadata()
    assert_equal('2.0', actual['swagger'])


def test_metadata_description():
    actual = build_metadata()
    assert_in('```', actual['info']['description'], 'Description should be Markdown')


def test_map_path_base_to_swagger_without_url():
    expected = {
        "summary": "Nombre d'enfants à charge titulaires de la carte d'invalidité",
        "tags": ["foy"]
        }

    actual = map_path_base_to_swagger({
        "@type": "Integer",
        "cerfa_field": "G",
        "default": 0,
        "entity": "foy",
        "label": "Nombre d'enfants à charge titulaires de la carte d'invalidité",
        "name": "nbG"
        })

    assert_equal(actual, expected)


def test_map_path_base_to_swagger_with_url():
    expected = {
        "summary": "Contribution exceptionnelle sur les hauts revenus",
        "tags": ["foy"],
        "externalDocs": {
            "url": "http://www.legifrance.gouv.fr/affichCode.do?"
                   "cidTexte=LEGITEXT000006069577&idSectionTA=LEGISCTA000025049019"
            }
        }

    actual = map_path_base_to_swagger({
        "@type": "Float",
        "default": 0,
        "entity": "foy",
        "label": "Contribution exceptionnelle sur les hauts revenus",
        "name": "cehr",
        "url": "http://www.legifrance.gouv.fr/affichCode.do?"
               "cidTexte=LEGITEXT000006069577&idSectionTA=LEGISCTA000025049019"
        })

    assert_equal(actual, expected)


def test_map_path_base_to_swagger_with_enum():
    expected = {
        "summary": "Catégorie de taille d'entreprise (pour calcul des cotisations sociales)",
        "tags": ["ind"]
        }

    actual = map_path_base_to_swagger({
        "@type": "Enumeration",
        "default": "0",
        "entity": "ind",
        "label": "Catégorie de taille d'entreprise (pour calcul des cotisations sociales)",
        "name": "taille_entreprise",
        "labels": {
            "0": "Non pertinent",
            "1": "Moins de 10 salariés",
            "2": "De 10 à 19 salariés",
            "3": "De 20 à 249 salariés",
            "4": "Plus de 250 salariés"
            }
        })

    assert_equal(actual, expected)


def test_map_type_to_swagger_integer():
    assert_equal(map_type_to_swagger('Integer'), {'type': 'integer', 'format': 'int32'})


def test_map_type_to_swagger_float():
    assert_equal(map_type_to_swagger('Float'), {'type': 'number', 'format': 'float'})


def test_map_type_to_swagger_date():
    assert_equal(map_type_to_swagger('Date'), {'type': 'string', 'format': 'date'})


def test_map_type_to_swagger_boolean():
    assert_equal(map_type_to_swagger('Boolean'), {'type': 'boolean'})


def test_map_type_to_swagger_string():
    assert_equal(map_type_to_swagger('String'), {'type': 'string'})


def test_map_type_to_swagger_enum():
    assert_equal(map_type_to_swagger('Enumeration'), {'type': 'string'})


def test_map_parameter_to_swagger():
    target_column = model.tax_benefit_system.variables['revenus_du_capital']

    expected = {
        'name': u'revenus_du_capital',
        'description': u'Revenus du patrimoine',
        'in': 'query',
        'type': 'number',
        'format': 'float',
        'default': 0
        }

    assert_equal(map_parameter_to_swagger(target_column), expected)


def test_map_enum_parameter_to_swagger():
    target_column = model.tax_benefit_system.variables['taille_entreprise']

    expected = {
        'name': u'taille_entreprise',
        'description': u"Cat\xe9gorie de taille d'entreprise",
        'in': 'query',
        'type': 'string',
        'enum': [
            u'Non pertinent',
            u'Moins de 10 salariés',
            u'De 10 à 19 salariés',
            u'De 20 à 249 salariés',
            u'Plus de 250 salariés',
            ],
        'default': u'Non pertinent',
        }

    assert_equal(map_parameter_to_swagger(target_column), expected)
