# -*- coding: utf-8 -*-


import json

from nose.tools import assert_equal, assert_greater, assert_in, assert_is_instance
from webob import Request

from . import common


def setup_module(module):
    common.get_or_load_app()


def test_basic_call():
    req = Request.blank('/api/1/variables', method = 'GET')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200, res.body)
    res_json = json.loads(res.body)
    assert_is_instance(res_json, dict)
    assert_in('country_package_name', res_json)
    assert_in('country_package_version', res_json)
    assert_in('variables', res_json)
    assert_is_instance(res_json['variables'], list)

    source_file_path = res_json['variables'][0]['source_file_path']
    assert source_file_path.startswith('model'), source_file_path
