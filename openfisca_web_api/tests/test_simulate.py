# -*- coding: utf-8 -*-


import json

from nose.tools import assert_equal, assert_in, assert_not_in
from webob import Request

from . import common


def setup_module(module):
    common.get_or_load_app()


def test_simulate_without_body():
    req = Request.blank('/api/1/simulate', headers = (('Content-Type', 'application/json'),), method = 'POST')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400)


def test_simulate_with_invalid_body():
    req = Request.blank(
        '/api/1/simulate',
        body = 'XXX',
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400)


def test_simulate_with_test_case():
    test_case = {
        'scenarios': [
            {
                'test_case': {
                    'familles': [
                        {
                            'parents': ['ind0', 'ind1'],
                            },
                        ],
                    'foyers_fiscaux': [
                        {
                            'declarants': ['ind0', 'ind1'],
                            },
                        ],
                    'individus': [
                        {'id': 'ind0', 'salaire_imposable': 15000},
                        {'id': 'ind1'},
                        ],
                    'menages': [
                        {
                            'conjoint': 'ind1',
                            'personne_de_reference': 'ind0',
                            },
                        ],
                    },
                'period': '2013',
                },
            ],
        }
    req = Request.blank(
        '/api/1/simulate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_body_json = json.loads(res.body)
    assert_not_in('error', res_body_json)
    assert_in('value', res_body_json)


def test_simulate_with_wrong_input_variable_period():
    test_case = {
        'scenarios': [
            {
                'test_case': {
                    'familles': [
                        {
                            'parents': ['ind0', 'ind1'],
                            },
                        ],
                    'foyers_fiscaux': [
                        {
                            'declarants': ['ind0', 'ind1'],
                            # rfr is defined for a year, its value can't be set for a month
                            'rfr': {"2013-01": 15000},
                            },
                        ],
                    'individus': [
                        {'id': 'ind0'},
                        {'id': 'ind1'},
                        ],
                    'menages': [
                        {
                            'conjoint': 'ind1',
                            'personne_de_reference': 'ind0',
                            },
                        ],
                    },
                'period': '2013',
                },
            ],
        }
    req = Request.blank(
        '/api/1/simulate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'Unable to set a value for variable', res_body_json['error']['message'], res.body)


def test_simulate_with_wrong_period():
    test_case = {
        'scenarios': [
            {
                'test_case': {
                    'familles': [
                        {
                            'parents': ['ind0'],
                            },
                        ],
                    'foyers_fiscaux': [
                        {
                            'declarants': ['ind0'],
                            },
                        ],
                    'individus': [
                        {'id': 'ind0'},
                        ],
                    'menages': [
                        {
                            'personne_de_reference': 'ind0',
                            },
                        ],
                    },
                'period': '2015-01',
                },
            ],
        }
    req = Request.blank(
        '/api/1/simulate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'ValueError: Unable to compute variable', res_body_json['error']['message'], res.body)
