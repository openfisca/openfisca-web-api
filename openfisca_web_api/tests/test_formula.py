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

from webob import Request
from nose.tools import assert_equal, assert_is_instance

from . import common


TARGET_URL = '/api/1/formula/salaire_net_a_payer'


def setup_module(module):
    common.get_or_load_app()


def test_formula_get_status_code():
    req = Request.blank(TARGET_URL, method = 'GET')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200)


def test_formula_post_status_code():
    req = Request.blank(TARGET_URL, method = 'POST')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 405)


def test_formula_put_status_code():
    req = Request.blank(TARGET_URL, method = 'PUT')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 405)


def test_formula_delete_status_code():
    req = Request.blank(TARGET_URL, method = 'DELETE')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 405)


def test_formula_value():
    req = Request.blank(TARGET_URL, method = 'GET')
    res = req.get_response(common.app)
    res_json = json.loads(res.body)
    assert_is_instance(res_json['value'], float)
