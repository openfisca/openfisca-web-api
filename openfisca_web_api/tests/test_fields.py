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

from nose.tools import assert_equal, assert_greater, assert_in, assert_is_instance
from webob import Request

from . import common


def setup_module(module):
    common.get_or_load_app()


def test_fields_without_parameters():
    req = Request.blank('/api/1/fields', method = 'GET')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_json = json.loads(res.body)
    assert_is_instance(res_json, dict)
    assert_in('columns', res_json)
    assert_in('columns_tree', res_json)
    assert_is_instance(res_json['columns'], dict)
    assert_is_instance(res_json['columns_tree'], dict)
    assert_greater(len(res_json['columns']), 0)
    assert_greater(len(res_json['columns_tree']), 0)
