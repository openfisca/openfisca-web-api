# -*- coding: utf-8 -*-


import json

from nose.tools import assert_equal, assert_is_instance, assert_true
from webob import Request

from . import common


def setup_module(module):
    common.get_or_load_app()


def test_calculate_without_body():
    req = Request.blank('/api/1/calculate', headers = (('Content-Type', 'application/json'),), method = 'POST')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400)


def test_calculate_with_invalid_body():
    req = Request.blank(
        '/api/1/calculate',
        body = 'XXX',
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400)


def test_calculate_with_test_case():
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
        'variables': ['revenu_disponible'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)


def test_calculate_with_axes():
    test_case = {
        'output_format': 'variables',
        "scenarios": [{
            "period": {
                "start": 2014,
                "unit": "year"
                },
            "axes": [{
                "count": 50,
                "max": 100000,
                "min": 0,
                "name": "salaire_imposable"
                }],
            "test_case": {
                "individus": [
                    {
                        "id": "Personne Principale",
                        "salaire_imposable": 0,
                        "statut_marital": 2
                        },
                    {
                        "id": "Personne Conjoint",
                        "salaire_imposable": 2
                        },
                    ],
                "familles": [{
                    "id": "Famille 1",
                    "parents": ["Personne Principale", "Personne Conjoint"],
                    "enfants": []
                    }],
                "foyers_fiscaux": [{
                    "id": "Déclaration d'impôt 1",
                    "declarants": ["Personne Principale", "Personne Conjoint"],
                    "personnes_a_charge": []
                    }],
                "menages": [{
                    "id": "Logement principal 1",
                    "personne_de_reference": "Personne Principale",
                    "conjoint": "Personne Conjoint",
                    "enfants": []
                    }],
                },
            }],
        'variables': ['impots_directs']
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_body_json = json.loads(res.body)
    impo_values = res_body_json['value'][0]['impots_directs']['2014']
    assert_is_instance(impo_values, list)
    assert_true(impo_values[-1] < 0)


def test_calculate_with_labels():
    # First test returning numeric values of enumerations.
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
                        {'id': 'ind0', 'categorie_salarie': 'prive_non_cadre'},
                        {'id': 'ind1', 'categorie_salarie': 'prive_cadre'},
                        ],
                    'menages': [
                        {
                            'conjoint': 'ind1',
                            'personne_de_reference': 'ind0',
                            },
                        ],
                    },
                'period': '2013-01',
                },
            ],
        'variables': ['categorie_salarie'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_body_json = json.loads(res.body)
    individus = res_body_json['value'][0]['individus']
    assert_equal(individus[0]['categorie_salarie']['2013-01'], 0)
    assert_equal(individus[1]['categorie_salarie']['2013-01'], 1)

    # Then test returning labels of enumerations.
    test_case['labels'] = True
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_body_json = json.loads(res.body)
    individus = res_body_json['value'][0]['individus']
    assert_equal(individus[0]['categorie_salarie']['2013-01'], 'prive_non_cadre')
    assert_equal(individus[1]['categorie_salarie']['2013-01'], 'prive_cadre')


def test_calculate_with_output_format_variables():
    test_case = {
        'output_format': 'variables',
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
        'variables': ['irpp'],
        }

    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_body_json = json.loads(res.body)
    value = res_body_json['value']
    assert_is_instance(value, list)
    assert_is_instance(value[0], dict)
    assert_equal(value[0].keys()[0], 'irpp')


def test_calculate_with_reform():
    test_case = {
        'base_reforms': ['trannoy_wasmer'],
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
                'period': '2013',
                },
            ],
        'variables': ['charge_loyer'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)


def test_calculate_with_trace():
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
                'period': '2014',
                },
            ],
        'trace': True,
        'variables': ['irpp'],
        }

    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_body_json = json.loads(res.body)
    tracebacks = res_body_json['tracebacks']
    assert_is_instance(tracebacks, list)
    first_scenario_tracebacks = tracebacks[0]
    assert_is_instance(first_scenario_tracebacks, list)
    first_traceback = first_scenario_tracebacks[0]
    assert_is_instance(first_traceback, dict)
    traceback_with_parameters = next(item for item in first_scenario_tracebacks if item.get('parameters'))
    assert_is_instance(traceback_with_parameters['parameters'], list)
