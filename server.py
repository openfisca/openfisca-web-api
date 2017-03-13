# -*- coding: utf-8 -*-

from flask import Flask, jsonify, abort

from .model import build_parameters

app = Flask(__name__)

parameters = build_parameters()
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
