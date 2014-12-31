# -*- coding: utf-8 -*-

import unittest

from openfisca_web_api.controllers import map_to_swagger, map_type_to_swagger

class TestSwagger(unittest.TestCase):
    def test_map_to_swagger_withour_url(self):
        expected = {
            "summary"      : "Nombre d'enfants à charge titulaires de la carte d'invalidité",
            "tags"         : [ "foy" ],
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

        actual = map_to_swagger({
            "@type": "Integer",
            "cerfa_field": "G",
            "default": 0,
            "entity": "foy",
            "label": "Nombre d'enfants à charge titulaires de la carte d'invalidité",
            "name": "nbG"
        })

        self.maxDiff = None
        self.assertEqual(actual, expected)

    def test_map_to_swagger_with_url(self):
        expected = {
            "summary"      : "Contribution exceptionnelle sur les hauts revenus",
            "tags"         : [ "foy" ],
            "externalDocs" : "http://www.legifrance.gouv.fr/affichCode.do?cidTexte=LEGITEXT000006069577&idSectionTA=LEGISCTA000025049019",
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

        actual = map_to_swagger({
            "@type": "Float",
            "default": 0,
            "entity": "foy",
            "label": "Contribution exceptionnelle sur les hauts revenus",
            "name": "cehr",
            "url": "http://www.legifrance.gouv.fr/affichCode.do?cidTexte=LEGITEXT000006069577&idSectionTA=LEGISCTA000025049019"
        })

        self.maxDiff = None
        self.assertEqual(actual, expected)

    def test_map_type_to_swagger_integer(self):
        self.assertEqual(map_type_to_swagger('Integer'), { 'type': 'integer', 'format': 'int32' })

    def test_map_type_to_swagger_float(self):
        self.assertEqual(map_type_to_swagger('Float'),   { 'type': 'number',  'format': 'float' })

    def test_map_type_to_swagger_date(self):
        self.assertEqual(map_type_to_swagger('Date'),    { 'type': 'string',  'format': 'date' })

    def test_map_type_to_swagger_boolean(self):
        self.assertEqual(map_type_to_swagger('Boolean'), { 'type': 'boolean' })

    def test_map_type_to_swagger_string(self):
        self.assertEqual(map_type_to_swagger('String'),  { 'type': 'string'  })


unittest.main()
