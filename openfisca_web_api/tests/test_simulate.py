# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
