# -*- coding: utf-8 -*-

from unittest import TestCase
import json

from openfisca_web_api.app import create_app

tester = create_app('openfisca_dummy_country').test_client()


class ParametersRoute(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.response = tester.get('/parameters')

    def test_return_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_headers(self):
        headers = self.response.headers
        self.assertEqual(headers.get('Country-Package'), 'openfisca-dummy-country')
        self.assertEqual(headers.get('Country-Package-Version'), '0.1.1')

    def test_item_content(self):
        parameters = json.loads(self.response.data)
        self.assertEqual(
            parameters[u'impot.taux'],
            { u'description': u'taux d\'impôt sur les salaires' }
            )


class ParameterRoute(TestCase):

    def test_error_code_non_existing_parameter(self):
        response = tester.get('/parameter/non.existing.parameter')
        self.assertEqual(response.status_code, 404)

    def test_return_code_existing_parameter(self):
        response = tester.get('/parameter/impot.taux')
        self.assertEqual(response.status_code, 200)

    def test_fuzzied_parameter_values(self):
        response = tester.get('/parameter/impot.taux')
        parameter = json.loads(response.data)
        self.assertEqual(
            parameter,
            {
                u'id': u'impot.taux',
                u'description': u'taux d\'impôt sur les salaires',
                u'values': {u'2016-01-01': 0.35, u'2015-01-01': 0.32, u'1998-01-01': 0.3}
                }
            )

    def test_stopped_parameter_values(self):
        response = tester.get('/parameter/csg.activite.deductible.taux')
        parameter = json.loads(response.data)
        self.assertEqual(
            parameter,
            {
                u'id': u'csg.activite.deductible.taux',
                u'description': u'taux de la CSG déductible',
                u'values': {u'2016-01-01': None, u'2015-01-01': 0.06, u'1998-01-01': 0.051}
                }
            )
