# -*- coding: utf-8 -*-


import json

from nose.tools import assert_equal, assert_in, assert_is_instance, assert_true
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
            "period": 2014,
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
                        "statut_marital": 'celibataire'
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
    assert_equal(individus[0]['categorie_salarie']['2013-01'], 'prive_non_cadre')
    assert_equal(individus[1]['categorie_salarie']['2013-01'], 'prive_cadre')

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


def test_calculate_with_intermediate_variables():
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
        'intermediate_variables': True,
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
    assert(res_body_json['value'][0]['familles'][0]['af_nbenf_fonc'])


def test_calculate_with_wrong_input_variable_period():
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
        'variables': ['revenu_disponible'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'Unable to set a value for variable rfr for month-long period 2013-01',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_wrong_variable_period():
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
                'period': '2013-01',
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'Unable to compute variable revenu_disponible for period 2013-01',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_wrong_input_variable():
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
                        {'id': 'ind0', 'i_do_not_exist': 42},
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'VariableNotFound: You tried to calculate or to set a value for variable \'i_do_not_exist\'',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_wrong_variable():
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
                'period': '2013',
                },
            ],
        'variables': ['i_do_not_exist'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'VariableNotFound: You tried to calculate or to set a value for variable \'i_do_not_exist\'',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_wrong_input_period_string():
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
                        {'id': 'ind0', 'enfant_a_charge': {'i_am_a_wrong_period': 42}},
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'period', res_body_json['error']['message'], res.body)
    assert_in(u'i_am_a_wrong_period', res_body_json['error']['message'], res.body)


def test_calculate_with_wrong_input_period_none():
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
                        {'id': 'ind0', 'enfant_a_charge': {None: 42}},
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'period', res_body_json['error']['message'], res.body)
    assert_in(u'null', res_body_json['error']['message'], res.body)


def test_calculate_with_wrong_period_string():
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
                'period': 'i_am_a_wrong_period_string',
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'period', res_body_json['error']['message'], res.body)
    assert_in(u'i_am_a_wrong_period_string', res_body_json['error']['message'], res.body)


def test_calculate_with_wrong_period_list():
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
                'period': ['i_am_a_wrong_period_list'],
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'period',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_input_variable_set_to_wrong_entity():
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
                            'salaire_imposable': 42,
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
        'variables': ['revenu_disponible'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'Variable salaire_imposable is defined for entity individu.',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_variable_with_set_input_and_inconsistent_input_data():
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
                            'loyer': {
                                '2013': 12000,
                                'month:2013-01:12': 1000,
                                },
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'Inconsistent input: variable loyer has already been set for all months '
        u'contained in period 2013, and value [ 12000.] provided for 2013 doesn\'t match the total ([ 999.99609375]).',
        res_body_json['error']['message'],
        res.body,
        )


def test_calculate_with_wrong_entity_name():
    test_case = {
        'scenarios': [
            {
                'test_case': {
                    'i_am_a_wrong_entity': [
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
        'variables': ['revenu_disponible'],
        }
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'Invalid entity name: i_am_a_wrong_entity', res_body_json['error']['message'], res.body)


def test_calculate_with_wrong_value_type():
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
                        {'id': 'ind0', 'salaire_imposable': [15000]},
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(
        u'Invalid value [15000] for variable salaire_imposable.',
        res_body_json['error']['message'], res.body
        )


def test_calculate_with_wrong_id_type():
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
                        {'id': {'k': 'ind0'}},
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
    assert_equal(res.status_code, 400, res.body)
    res_body_json = json.loads(res.body)
    assert_in(u'Invalid id in entity', res_body_json['error']['message'], res.body)
