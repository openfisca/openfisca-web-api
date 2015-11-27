# -*- coding: utf-8 -*-


import json

from nose.tools import assert_equal, assert_in, assert_is_instance
from webob import Request

from . import common


def setup_module(module):
    common.get_or_load_app()


def test_field_without_parameters():
    req = Request.blank('/api/1/field', method = 'GET')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_json = json.loads(res.body)
    assert_is_instance(res_json, dict)
    assert_in('value', res_json)
    assert_is_instance(res_json['value'], dict)
    assert_in('name', res_json['value'])
    assert_is_instance(res_json['value']['name'], basestring)
