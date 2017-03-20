# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, abort

from model import build_parameters

def create_app(country_package = os.environ.get('COUNTRY_PACKAGE')):
    if country_package is None:
        raise ValueError(u"You must specify a country package to start the api. For instance, COUNTRY_PACKAGE=openfisca_france flask run")

    app = Flask(__name__)

    parameters = build_parameters(country_package)
    parameters_description = {
        name: { 'description' :parameter['description']}
        for name, parameter in parameters.iteritems()
        }

    @app.route('/parameters')
    def get_parameters():
        return jsonify(parameters_description);


    @app.route('/parameter/<id>')
    def get_parameter(id):
        parameter = parameters.get(id)
        if parameter is None:
            raise abort(404)
        else:
            return jsonify(parameter)

    return app
