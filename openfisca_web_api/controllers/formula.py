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


"""Formula controller"""


from datetime import datetime

import numpy as np
from openfisca_core import periods, simulations

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api1_formula(req):
    params = dict(req.GET)

    try:
        period = get_period(params)
        params = normalize(params)
        column = get_column_from_formula_name(req.urlvars.get('name'))
        value = compute(column.name, params, period)

        return respond(req, dict(value = value), params)

    except Exception as error:
        return respond(req, dict(error = error.args[0]), params)


def get_column_from_formula_name(formula_name):
    result = model.tax_benefit_system.column_by_name.get(formula_name)
    if result is None:
        raise(Exception(dict(
            code = 404,
            message = u"You requested to compute variable '{}', but it does not exist"
                      .format(formula_name)
            )))

    if result.formula_class.function is None:
        raise(Exception(dict(
            code = 422,
            message = u"You requested to compute variable '{}', but it is an input variable, it cannot be computed"
                      .format(formula_name)
            )))

    return result


def normalize(params):
    result = dict()

    try:
        for param_name, value in params.items():
            result[param_name] = normalize_param(param_name, value)
    except KeyError:
        raise Exception(dict(
            code = 400,
            message = u"You passed parameter '{}', but it does not exist".format(param_name)
            ))

    return result


def normalize_param(name, value):
    column = model.tax_benefit_system.column_by_name[name]

    result, error = conv.pipe(
        column.input_to_dated_python  # if column is not a date, this will be None and conv.pipe will be pass-through
        )(value)

    if error is not None:
        raise Exception(dict(
            code = 400,
            message = u"Parameter '{}' could not be normalized: {}".format(name, error)
            ))

    return result


def get_period(params):
    now = datetime.now()
    default = '{}-{}'.format(now.year, now.month)

    result = params.pop('period', default)

    try:
        return periods.period(result)
    except ValueError:
        raise(Exception(dict(
            code = 400,
            message = "You requested computation for period '{}', but it could not be parsed as a period".format(result)
            )))


# req: the original request we're responding to.
# data: dict. Will be transformed to JSON and added to the response root.
#       `data` will be mutated. Currently considered acceptable because responding marks process end.
# params: dict. Parsed parameters. Will be echoed in the "params" key.
def respond(req, data, params):
    data.update(dict(
        apiVersion = 1,
        params = params
        ))

    ctx = contexts.Ctx(req)

    return wsgihelpers.respond_json(
        ctx,
        data,
        headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)
        )


def compute(formula_name, params, period):
    simulation = create_simulation(params, period)
    resulting_dated_holder = simulation.compute(formula_name)
    return resulting_dated_holder.to_value_json()[0]  # only one person => unwrap the array


def create_simulation(data, period):
    result = simulations.Simulation(
        debug = False,
        period = period,
        tax_benefit_system = model.tax_benefit_system,
        )
    # Initialize entities, assuming there is only one person and one of each other entities ("familles",
    # "foyers fiscaux", etc).
    persons = None
    for entity in result.entity_by_key_plural.itervalues():
        entity.count = 1
        entity.roles_count = 1
        entity.step_size = 1
        if entity.is_persons_entity:
            persons = entity
    # Link person to its entities using ID & role.
    for entity in result.entity_by_key_plural.itervalues():
        if not entity.is_persons_entity:
            holder = persons.get_or_new_holder(entity.index_for_person_variable_name)
            holder.set_array(period, np.array([0]))
            holder = persons.get_or_new_holder(entity.role_for_person_variable_name)
            holder.set_array(period, np.array([0]))
    # Inject all variables from query string into arrays.
    for column_name, value in data.iteritems():
        column = model.tax_benefit_system.column_by_name[column_name]
        entity = result.entity_by_key_plural[column.entity_key_plural]
        holder = entity.get_or_new_holder(column_name)
        holder.set_array(period, np.array([value], dtype = column.dtype))

    return result
