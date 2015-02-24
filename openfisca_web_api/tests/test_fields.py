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

from . import common


def setup_module(module):
    common.get_or_load_app()


def test_field_without_parameters():
    req = Request.blank('/api/1/field', method = 'GET')
    res = req.get_response(common.app)
    assert res.status_code == 200, res.status_code
    res_json = json.loads(res.body)
    assert isinstance(res_json, dict), res_json
    assert 'value' in res_json, res_json
    assert isinstance(res_json['value'], dict), res_json
    assert 'name' in res_json['value'], res_json



def test_fields_without_parameters():
    req = Request.blank('/api/1/fields', method = 'GET')
    res = req.get_response(common.app)
    assert res.status_code == 200, res.status_code
    res_json = json.loads(res.body)
    assert isinstance(res_json, dict), res_json
    assert 'columns' in res_json, res_json
    assert 'columns_tree' in res_json, res_json
    assert isinstance(res_json['columns'], dict), res_json
    assert isinstance(res_json['columns_tree'], dict), res_json
    assert len(res_json['columns']) > 0, res_json
    assert len(res_json['columns_tree']) > 0, res_json
