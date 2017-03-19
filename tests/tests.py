# -*- coding: utf-8 -*-

from unittest import TestCase
import json

from openfisca_web_api.server import app

tester = app.test_client()

class ParametersRoute(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.response = tester.get('/parameters')

    def test_return_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_item_content(self):
        parameters = json.loads(self.response.data)
        self.assertEqual(
            parameters['cotsoc.gen.smic_h_b'],
            { 'description': 'SMIC horaire brut' }
            )


class ParameterRoute(TestCase):

    def test_error_code_non_existing_parameter(self):
        response = tester.get('/parameter/non.existing.parameter')
        self.assertEqual(response.status_code, 404)

    def test_return_code_existing_parameter(self):
        response = tester.get('/parameter/prestations.minima_sociaux.rsa.montant_de_base_du_rsa')
        self.assertEqual(response.status_code, 200)
