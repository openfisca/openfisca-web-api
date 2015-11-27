# -*- coding: utf-8 -*-


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
