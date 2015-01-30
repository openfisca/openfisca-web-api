# -*- coding: utf-8 -*-

import unittest

import os

from openfisca_web_api import environment, model
from paste.deploy import appconfig
from openfisca_web_api.controllers.swagger import (
    map_path_base_to_swagger,
    map_type_to_swagger,
    map_parameters_to_swagger,
    map_parameter_to_swagger,
    )


class TestSwagger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ini_file_path = os.path.join(os.path.dirname(__file__), '../../development-france.ini')
        site_conf = appconfig('config:' + os.path.abspath(ini_file_path) + '#main')
        environment.load_environment(site_conf.global_conf, site_conf.local_conf)

    def test_map_path_base_to_swagger_withour_url(self):
        expected = {
            "summary": "Nombre d'enfants à charge titulaires de la carte d'invalidité",
            "tags": ["foy"],
            "responses": {
                200: {
                    "description": "Nombre d'enfants à charge titulaires de la carte d'invalidité",
                    "schema": {
                        "type": "integer",
                        "format": "int32"
                    }
                }
            }
        }

        actual = map_path_base_to_swagger({
            "@type": "Integer",
            "cerfa_field": "G",
            "default": 0,
            "entity": "foy",
            "label": "Nombre d'enfants à charge titulaires de la carte d'invalidité",
            "name": "nbG"
        })

        self.maxDiff = None
        self.assertEqual(actual, expected)

    def test_map_path_base_to_swagger_with_url(self):
        expected = {
            "summary": "Contribution exceptionnelle sur les hauts revenus",
            "tags": ["foy"],
            "externalDocs": {
                "url": "http://www.legifrance.gouv.fr/affichCode.do?"
                       "cidTexte=LEGITEXT000006069577&idSectionTA=LEGISCTA000025049019"
            },
            "responses": {
                200: {
                    "description": "Contribution exceptionnelle sur les hauts revenus",
                    "schema": {
                        "type": "number",
                        "format": "float"
                    }
                }
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

        self.maxDiff = None
        self.assertEqual(actual, expected)

    def test_map_path_base_to_swagger_with_enum(self):
        expected = {
            "summary": "Catégorie de taille d'entreprise (pour calcul des cotisations sociales)",
            "tags": ["ind"],
            "responses": {
                200: {
                    "description": "Catégorie de taille d'entreprise (pour calcul des cotisations sociales)",
                    "schema": {
                        "type": "string"
                    }
                }
            }
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

        self.maxDiff = None
        self.assertEqual(actual, expected)

    def test_map_type_to_swagger_integer(self):
        self.assertEqual(map_type_to_swagger('Integer'), {'type': 'integer', 'format': 'int32'})

    def test_map_type_to_swagger_float(self):
        self.assertEqual(map_type_to_swagger('Float'), {'type': 'number', 'format': 'float'})

    def test_map_type_to_swagger_date(self):
        self.assertEqual(map_type_to_swagger('Date'), {'type': 'string', 'format': 'date'})

    def test_map_type_to_swagger_boolean(self):
        self.assertEqual(map_type_to_swagger('Boolean'), {'type': 'boolean'})

    def test_map_type_to_swagger_string(self):
        self.assertEqual(map_type_to_swagger('String'), {'type': 'string'})

    def test_map_type_to_swagger_enum(self):
        self.assertEqual(map_type_to_swagger('Enumeration'), {'type': 'string'})

    def test_map_parameters_to_swagger(self):
        self.maxDiff = None

        target_column = model.tax_benefit_system.column_by_name['revdisp']

        actual = [
            description.get('name')
            for description in map_parameters_to_swagger(target_column)
        ]

        self.assertEqual(actual, ['ppe', 'rev_trav', 'rev_cap', 'pen', 'psoc', 'impo'])

    def test_map_parameter_to_swagger(self):
        self.maxDiff = None

        target_column = model.tax_benefit_system.column_by_name['rev_cap']

        expected = {
            'name': u'rev_cap',
            'description': u'Revenus du patrimoine',
            'in': 'query',
            'type': 'number',
            'format': 'float',
            'default': 0
        }

        self.assertEqual(map_parameter_to_swagger(target_column), expected)

    def test_map_enum_parameter_to_swagger(self):
        self.maxDiff = None

        target_column = model.tax_benefit_system.column_by_name['taille_entreprise']

        expected = {
            'name': u'taille_entreprise',
            'description': u"Catégode taille d'entreprise (pour calcul des cotisations sociales)",
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

        self.assertEqual(map_parameter_to_swagger(target_column), expected)


if __name__ == '__main__':
    unittest.main()
