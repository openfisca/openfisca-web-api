# API endpoints

## calculate

Launch a simulation with an input test case, returning the computation results.

* URL path: `/api/1/calculate`
* method: POST
* required headers:
  * `Content-Type: application/json`
* JSON request structure:
  * `context` (string, default: null): returned as is in the JSON response
  * `output_format` (string, one of ["test_case", "vector"], default: "test_case"): the output format of `value` field in response.
    * `test_case`: `value` will be a list of test cases identical to the input test cases given in `scenarios` key, with computed variables dispatched in the right entity.
    * `vector`: `value` will be a list of objects like `{<variableName>: <variableValue>}`
  * `scenarios` (list of objects): a list of test cases, see [scenarios](#scenarios)
  * `trace` (boolean, default: false): when true a traceback
  * `validate` (boolean, default: false): when true the simulation isn't launched, but the scenarios are validated
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
  * `scenarios` (list of objects): a list of test cases, see [scenarios](#scenarios)
  * `trace` (boolean, default: false): when true a traceback
  * `validate` (boolean, default: false): when true the simulation isn't launched, but the scenarios are validated
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

## input variables values

JSON input variables values can be:

* a scalar value (string, integer, boolean). In this case the value is defined on the period of the scenario.
* an object which key is a period (see [periods](#periods)) and the value is a scalar value.

JSON input values are intended to be set in a [JSON test case](#test-cases).

## periods

JSON periods can be:

* a `string` like "2014", "2014-01", "2014-03:2"
* an `object` like `{start: 2014, unit: "year"}`

The Python function used to parse a JSON period is
[`make_json_or_python_to_period`](https://github.com/openfisca/openfisca-core/blob/master/openfisca_core/periods.py#L1067) (given examples).

## scenarios

JSON scenarios are structured this way:
* `period` (a string or an object, see [periods](#periods), default: ): the variables in the decomposition will be computed on this period
* `test_case` (an object): the test case of the scenario, see [test cases](#test-cases)

## test cases

A test case describes persons, entities and their associations.

JSON test cases are structured this way:

* `individus` (list of objects): defines persons with their input variables, structured this way:
  * `id` (string): the ID of the person
  * `<input variable name (string)>` ([JSON input variable value](#input-variables-values))
* `<entity key plural (string)>` (list of objects): the definition of the entity, structured this way:
  * `id` (string): the ID of the entity
  * `<role key (string)>` (list of strings): a list of persons IDs referencing the ones defined under the individus key
  * `<input variable name (string)>` ([JSON input variable value](#input-variables-values))

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

# Deprecated API endpoints

## field

> Deprecated, replaced by the `variables` endpoint.

Get info about a variable.

* URL path: `/api/1/field`
* GET parameters:
  * `context` (string, default: null): returned as is in the JSON response
  * `input_variables` (boolean, default: true): whether input variables info is inserted in each variable formula
  * `reform` (list of strings (one of [declared reforms](#reforms)), default: null): the reforms to load in order to know the variables they contain
  * `variable` (string, default: "revdisp", one of available [variable names](http://legislation.openfisca.fr/variables)): the name of the variable to query
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
