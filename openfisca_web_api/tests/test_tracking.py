# -*- coding: utf-8 -*-

from webob import Request
import time
import json
import logging
from . import common

ACTIVE_TRACKING = True
log = logging.getLogger(__name__)


def setup_module(module):
    if ACTIVE_TRACKING:
        common.get_or_load_tracked_app()
    else:
        common.get_or_load_app()


# Test that the tracking doesn't affect original request
def test_entities_without_parameters():
    req = Request.blank('/api/2/entities', method = 'GET')
    res = req.get_response(common.app)
    assert res.status_code == 200


def time_requests(nb_requests, url, method, headers = None, body = None):
    start_time = time.time()
    requests = []
    for i in range(nb_requests):
        requests.append(Request.blank(url, method = method, headers = headers, body = body))

    for req in requests:
        yield req.get_response(common.app)

    exec_time = time.time() - start_time
    log.info('{:2.6f} s'.format(exec_time))


def test_multiple_requests__variables():
    time_requests(100, '/api/1/variables', 'GET')


def test_multiple_requests__calculate():
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
    time_requests(100, '/api/1/calculate', 'POST', headers = (('Content-Type', 'application/json'),), body = json.dumps(test_case))
