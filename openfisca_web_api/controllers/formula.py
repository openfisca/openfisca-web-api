# -*- coding: utf-8 -*-


"""Formula controller"""


from datetime import datetime

import numpy as np
from openfisca_core import periods, simulations
from openfisca_core.taxbenefitsystems import VariableNotFound

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api1_formula(req):
    API_VERSION = 1
    params = dict(req.GET)
    data = dict()

    try:
        tax_benefit_system = model.tax_benefit_system
        period = parse_period(params.pop('period', None))
        params = normalize(params, tax_benefit_system)
        column = get_column_from_formula_name(req.urlvars.get('name'), tax_benefit_system)
        simulation = create_simulation(params, period, tax_benefit_system)
        data['value'] = compute(column.name, simulation)
    except Exception as error:
        data['error'] = error.args[0]
    finally:
        return respond(req, API_VERSION, data, params)


@wsgihelpers.wsgify
def api2_formula(req):
    """
A simple `GET`-, URL-based API to OpenFisca, making the assumption of computing formulas for a single person.

Combination
-----------

You can compute several formulas at once by combining the paths and joining them with `+`.

Example:
```
/salaire_super_brut+salaire_net_a_payer?salaire_de_base=1440
```

This will compute both `salaire_super_brut` and `salaire_net_a_payer` in a single request.

Reforms
-----------

Reforms can be requested to patch the simulation system.
To keep this endpoint URL simple, they are requested as a list in a custom HTTP header.
```
X-OpenFisca-Extensions: de_net_a_brut, landais_piketty_saez
```
This header is of course optional.


URL size limit
--------------

Using combination with a lot of parameters may lead to long URLs.
If used within the browser, make sure the resulting URL is kept
[under 2047 characters](http://stackoverflow.com/questions/417142)
for cross-browser compatibility, by splitting combined requests.
On a server, just test what your library handles.
"""
    API_VERSION = '2.1.0'
    params = dict(req.GET)
    data = dict()

    try:
        extensions_header = req.headers.get('X-Openfisca-Extensions')

        tax_benefit_system = model.get_cached_composed_reform(
            reform_keys = extensions_header.split(','),
            tax_benefit_system = model.tax_benefit_system,
            ) if extensions_header is not None else model.tax_benefit_system

        params = normalize(params, tax_benefit_system)
        formula_names = req.urlvars.get('names').split('+')

        data['values'] = dict()
        data['period'] = parse_period(req.urlvars.get('period'))

        simulation = create_simulation(params, data['period'], tax_benefit_system)

        for formula_name in formula_names:
            column = get_column_from_formula_name(formula_name, tax_benefit_system)
            data['values'][formula_name] = compute(column.name, simulation)

    except Exception as error:
        if isinstance(error.args[0], dict):  # we raised it ourselves, in this controller
            error = error.args[0]
        else:
            error = dict(
                message = unicode(error),
                code = 500
                )

        data['error'] = error
    finally:
        return respond(req, API_VERSION, data, params)


def get_column_from_formula_name(formula_name, tax_benefit_system):
    try:
        result = tax_benefit_system.get_column(formula_name, check_existence = True)
    except VariableNotFound as exc:
        raise Exception(dict(
            code = 404,
            message = exc.message
            ))

    if result.is_input_variable():
        raise Exception(dict(
            code = 422,
            message = u"You requested to compute variable '{}', but it is an input variable, it cannot be computed"
                      .format(formula_name)
            ))

    return result


def normalize(params, tax_benefit_system):
    result = dict()

    try:
        for param_name, value in params.items():
            result[param_name] = normalize_param(param_name, value, tax_benefit_system)
    except VariableNotFound as exc:
        raise Exception(dict(
            code = 400,
            message = exc.message
            ))
    return result


def normalize_param(name, value, tax_benefit_system):
    column = tax_benefit_system.get_column(name, check_existence = True)

    result, error = conv.pipe(
        column.input_to_dated_python  # if column is not a date, this will be None and conv.pipe will be pass-through
        )(value)

    if error is not None:
        raise Exception(dict(
            code = 400,
            message = u"Parameter '{}' could not be normalized: {}".format(name, error)
            ))

    return result


def parse_period(period_descriptor):
    period_descriptor = period_descriptor or default_period()

    try:
        result = periods.period(period_descriptor)
    except ValueError:
        raise Exception(dict(
            code = 400,
            message = u"You requested computation for period '{}', but it could not be parsed as a period"
                      .format(period_descriptor)
            ))

    if result.unit not in ['year', 'month']:
        raise Exception(dict(
            code = 400,
            message = u"You passed period '{}', but it is not a month nor a year".format(period_descriptor)
            ))

    return result


def default_period():
    now = datetime.now()
    return '{}-{:02d}'.format(now.year, now.month)


# req: the original request we're responding to.
# version: a [semver](http://semver.org) identifier characterizing the version of the API.
# data: dict. Will be transformed to JSON and added to the response root.
#       `data` will be mutated. Currently considered acceptable because responding marks process end.
# params: dict. Parsed parameters. Will be echoed in the "params" key.
def respond(req, version, data, params):
    data.update(dict(
        apiVersion = version,
        params = params
        ))

    ctx = contexts.Ctx(req)

    return wsgihelpers.respond_json(
        ctx,
        data,
        headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx),
        json_dumps_default = wsgihelpers.convert_date_to_json,
        )


def compute(formula_name, simulation):
    resulting_dated_holder = simulation.compute(formula_name, simulation.period)
    return resulting_dated_holder.to_value_json()[0]  # only one person => unwrap the array


def create_simulation(data, period, tax_benefit_system):
    result = simulations.Simulation(
        debug = False,
        period = period,
        tax_benefit_system = tax_benefit_system,
        )
    # Initialize entities, assuming there is only one person and one of each other entities ("familles",
    # "foyers fiscaux", etc).
    for entity in result.entities.itervalues():
        entity.count = 1
        entity.roles_count = 1
        entity.step_size = 1
    # Link person to its entities using ID & role.
    for entity in result.entities.itervalues():
        if not entity.is_person:
            entity.members_entity_id = np.array([0])
            entity.members_legacy_role = np.array([0])
            entity.members_role = np.array([0])

    # Inject all variables from query string into arrays.
    for column_name, value in data.iteritems():
        column = tax_benefit_system.column_by_name[column_name]
        holder = result.get_or_new_holder(column_name)

        if period.unit == 'year':
            holder.put_in_cache(np.array([value], dtype = column.dtype), period)
        elif period.unit == 'month':
            # Inject inputs for all months of year
            year = period.start.year
            month_index = 1
            while month_index <= 12:
                month = periods.period('{}-{:02d}'.format(year, month_index))
                holder.put_in_cache(np.array([value], dtype = column.dtype), month)
                month_index += 1

    return result
