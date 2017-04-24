# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, abort
from flask_cors import CORS

from model import build_parameters, build_tax_benefit_system, build_headers, build_variables


def create_app(country_package = os.environ.get('COUNTRY_PACKAGE')):
    if country_package is None:
        raise ValueError(
            u"You must specify a country package to start the API. "
            u"For instance, `COUNTRY_PACKAGE=openfisca_france flask run`"
            .encode('utf-8')
            )

    app = Flask(__name__)
    CORS(app, origins = '*')

    tax_benefit_system = build_tax_benefit_system(country_package)
    headers = build_headers(tax_benefit_system)
    parameters = build_parameters(tax_benefit_system)
    parameters_description = {
        name: {'description': parameter['description']}
        for name, parameter in parameters.iteritems()
        }
    variables = build_variables(tax_benefit_system)
    variables_description = {
        name: {'description': variable['description']}
        for name, variable in variables.iteritems()
        }

    app.url_map.strict_slashes = False  # Accept url like /parameters/

    @app.route('/parameters')
    def get_parameters():
        return jsonify(parameters_description)

    @app.route('/parameter/<id>')
    def get_parameter(id):
        parameter = parameters.get(id)
        if parameter is None:
            raise abort(404)
        return jsonify(parameter)

    @app.route('/variables')
    def get_variables():
        return jsonify(variables_description)

    @app.route('/variable/<id>')
    def get_variable(id):
        variable = variables.get(id)
        if variable is None:
            raise abort(404)
        return jsonify(variable)

    @app.after_request
    def apply_headers(response):
        response.headers.extend(headers)
        return response

    return app
