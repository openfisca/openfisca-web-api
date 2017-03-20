# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, abort

from model import build_parameters, build_tax_benefit_system, build_headers


def create_app(country_package = os.environ.get('COUNTRY_PACKAGE')):
    if country_package is None:
        raise ValueError(
            u"You must specify a country package to start the API. "
            u"For instance, `COUNTRY_PACKAGE=openfisca_france flask run`"
            .encode('utf-8')
            )

    app = Flask(__name__)

    tax_benefit_system = build_tax_benefit_system(country_package)
    headers = build_headers(tax_benefit_system)
    parameters = build_parameters(tax_benefit_system)
    parameters_description = {
        name: {'description': parameter['description']}
        for name, parameter in parameters.iteritems()
        }

    @app.route('/parameters')
    def get_parameters():
        return jsonify(parameters_description)

    @app.route('/parameter/<id>')
    def get_parameter(id):
        parameter = parameters.get(id)
        if parameter is None:
            raise abort(404)
        else:
            return jsonify(parameter)

    @app.after_request
    def apply_headers(response):
        response.headers.extend(headers)
        return response

    return app
