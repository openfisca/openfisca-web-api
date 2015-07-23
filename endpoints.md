# API endpoints

## calculate

Launch a simulation with an input test case, returning the computation results.

* URL path: `/api/1/calculate`
* method: POST
* required headers:
  * `Content-Type: application/json`
* JSON request structure:
  * `context` (string, default: null): returned as is in the JSON response
  * `output_format` (string, one of ["test_case", "variables"], default: "test_case"): the output format of `value` field in response.
    * `test_case`: `value` will be a list of test cases identical to the input test cases given in `scenarios` key, with computed variables dispatched in the right entity.
    * `variables`: `value` will be a list of objects like `{<variableName>: <variableValue>}`
  * `scenarios` (list of objects): a list of [scenarios](#scenarios)
  * `trace` (boolean, default: false): when true a traceback
  * `validate` (boolean, default: false): when true the simulation isn't launched, but the scenarios are [validated](#scenarios-validation)
  * `variables` (list of strings, one of available [variable names](http://legislation.openfisca.fr/variables)): the name of the variables to compute
* JSON response structure:
  * `suggestions` (list of objects): suggested variables values for the input test_case, actually used by the simulation. Different than variables default values since it depends on the input test_case.
  * `tracebacks` (list of TODO, if trace is true in request body): TODO
  * `variables` (list of TODO, if trace is true in request body): TODO
  * `value` (list or object, depending on the `output_format` value): The simulation result.
    Each output variable value is a list which length is equal to the number of entities on which the variable is defined.

## entities

Get the entities metadata.

TODO

Example: http://api.openfisca.fr/api/1/entities

## formula

TODO

## graph

Get the graph (nodes and edges) of the variables called during the computation of the given variable.

* URL path: `/api/1/graph`
* GET parameters:
  * `context` (string, default: null): returned as is in the JSON response
  * `variable` (string, default: "revdisp", one of available [variable names](http://legislation.openfisca.fr/variables)): the name of the variable to query
* JSON response structure:
  * `edges` (list of objects): the oriented edges between the nodes, representing a variable dependency
  * `nodes` (list of objects): the nodes representing variables

Example: http://api.openfisca.fr/api/1/graph?variable=zone_apl

## parameters

Get information about legislation parameters.

TODO

Example: http://api-test.openfisca.fr/api/1/parameters

## reforms

Get the list of declared reforms.

TODO

Example: http://api-test.openfisca.fr/api/1/reforms

## simulate

Launch a simulation with an input test case, returning the computation results dispatched in a JSON decomposition
based on [decomp.xml](https://github.com/openfisca/openfisca-france/blob/master/openfisca_france/decompositions/decomp.xml).

* URL path: `/api/1/simulate`
* method: POST
* required headers:
  * `Content-Type: application/json`
* JSON request structure:
  * `context` (string, default: null): returned as is in the JSON response
  * `scenarios` (list of objects): a list of [scenarios](#scenarios)
  * `trace` (boolean, default: false): when true a traceback
  * `validate` (boolean, default: false): when true the simulation isn't launched, but the scenarios are [validated](#scenarios-validation)
* JSON response structure:
  * `suggestions` (list of objects): suggested variables values for the input test_case, actually used by the simulation. Different than variables default values since it depends on the input test_case.
  * `tracebacks` (list of TODO, if trace is true in request body): TODO
  * `variables` (list of TODO, if trace is true in request body): TODO
  * `value` (object): the simulation result

## swagger

TODO

## variables

Get information about simulation variables.

TODO

Example: http://api-test.openfisca.fr/api/1/variables

# JSON data structures

## axes

A JSON axis is an object structured this way:
* `count` (integer, >= 1, required): the number of steps to go from min to max
* `index` (integer, >= 0, default: 0): the index of the person on which to apply the variation of the variable
* `max` (integer or float, required): the maximum value of the varying variable
* `min` (integer or float, required): the minimum value of the varying variable
* `name` (string, one of available [variable names](http://legislation.openfisca.fr/variables), required): the name of the varying variable
* `period` (a JSON period):

### Parallel axes

TODO

### Perpendicular axes

TODO

## periods

A JSON period can be:
* a `string` like "2014", "2014-01", "2014-03:2"
* an `object` like `{start: "2014", unit: "year"}`

The Python function used to parse a JSON period is
[`make_json_or_python_to_period`](https://github.com/openfisca/openfisca-core/blob/master/openfisca_core/periods.py#L1067) (see examples).

## scenarios

A JSON scenario is an object structured this way:
* `axes` (a list of objects, default: null): the axes of the scenario, see [axes](#axes)
* `input_variables` (an object, mutually exclusive with `test_case`): the input variables, structured this way:
  * `<variable name (string)>` (the [JSON variable value](#variables-values)): an input variable
* `period` (a [JSON period](#periods), default: the current year): the period on which the variables of the decomposition will be computed
* `test_case` (an object, mutually exclusive with `input_variables`): the test case of the scenario, see [test cases](#test-cases)

> Either `test_case` or `input_variables` must be provided, not both.

> `axes` can't be used with `input_variables`, only `test_case`.

## test cases

A test case describes persons, entities and their associations.

A JSON test case is an object structured this way:
* `individus` (list of objects): defines persons with their input variables, structured this way:
  * `id` (string): the ID of the person
  * `<variable name (string)>` (the [JSON variable value](#variables-values)): an input variable
* `<entity key plural (string)>` (list of objects): the definition of the entity, structured this way:
  * `id` (string): the ID of the entity
  * `<role key (string)>` (list of strings): a list of persons IDs referencing the ones defined under the individus key
  * `<variable name (string)>` (the [JSON variable value](#variables-values)): an input variable

Entities and roles can be fetched dynamically with the [entities](#entities) API endpoint.

Example:

```
{
  "individus": [
    {
      "id": "Personne 1",
      "salaire_de_base": 50000
    }
  ],
  "familles": [
    {
      "id": "Famille 1",
      "parents": ["Personne 1"]
    }
  ],
  "foyers_fiscaux": [
    {
      "id": "Déclaration d'impôt 1",
      "declarants": ["Personne 1"]
    }
  ],
  "menages": [
    {
      "id": "Logement principal 1",
      "personne_de_reference": "Personne 1"
    }
  ]
}
```

## variables values

A JSON variable value can be:
* a scalar value: string, integer, boolean. In this case the period is taken in the scenario.
* a vector: a list of scalar values.
* an object structured this way:
  * `<period>` ([JSON period](#periods)): a scalar value or a vector

JSON variables values can be found in [JSON test cases](#test-cases) or in [JSON input variables](#input-variables).

Examples:

```
20000
true
[20, 30, 40]
{"2014": 5000}
{"2014-01": [50, 100]}
```

# Common features

## Scenarios validation

TODO

# Deprecated API endpoints

## field

> Deprecated, replaced by the `variables` endpoint.

Get info about a variable.

* URL path: `/api/1/field`
* GET parameters:
  * `context` (string, default: null): returned as is in the JSON response
  * `input_variables` (boolean, default: true): whether input variables info is inserted in each variable formula
  * `reform` (list of strings (one of [declared reforms](#reforms)), default: null): the reforms to load in order to know the variables they contain
  * `variable` (string, one of available [variable names](http://legislation.openfisca.fr/variables), default: "revdisp"): the name of the variable to query
* JSON response structure:
  * TODO

Example: http://api.openfisca.fr/api/1/field?variable=irpp

## fields

> Deprecated, replaced by the `variables` endpoint.

Get info about all known variables.

* URL path: `/api/1/fields`
* GET parameters:
  * `context` (string, default: null): returned as is in the response JSON body
* JSON response structure:
  * `columns`: list of input variables
  * `columns_tree`: tree of input variables grouped by entity name and by arbitrary categories.
    Intended to help building user interface.
  * `prestations`: list of calculated variables

Example: http://api.openfisca.fr/api/1/fields
