# -*- coding: utf-8 -*-

import time
import json
import logging
import sys
from webob import Request
from openfisca_web_api.tests import common
log = logging.getLogger(__name__)

if len(sys.argv) >= 2 and sys.argv[1] == '--tracking':
    print('Testing performances with tracking')
    common.app = common.get_or_load_tracked_app()
else:

    print('Testing performances without tracking')
    common.app = common.get_or_load_app()


def time_requests(nb_requests, url, method, headers = None, body = None):
    start_time = time.time()
    requests = []
    for i in range(nb_requests):
        if i % 10 == 0:
            print(i)
        request = Request.blank(url, method = method, headers = headers, body = body)
        request.get_response(common.app)

    exec_time = time.time() - start_time
    print('{:2.6f} s'.format(exec_time))


# Request without body


def test_multiple_requests__parameters():
    time_requests(100, '/api/1/parameters', 'GET')


# Request with json body


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
    time_requests(100, '/api/1/calculate', 'POST',
                  headers = (('Content-Type', 'application/json'),),
                  body = json.dumps(test_case))


test_multiple_requests__parameters()
test_multiple_requests__calculate()
