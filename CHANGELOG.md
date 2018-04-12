# Changelog

## 8.2.0

* Adapt to Core v23

## 8.1.1

* Remove explicit dependency towards numpy

## 8.1.0

* Declare package compatible with core v22

## 8.0

* Use a string instead of an int to indicate an Enum item in the JSON request and response
* Make the web API compatible with Core v21

## 7.2.0

* Make the web API compatible with Core v20

## 7.1.0

* Declare the web API compatible with Core v19

# 7.0.0

* Deprecate and remove `trace` parameter in `/calculate` and `/simulate` routes.
* Make API compatible with Core v19

## 6.2.2

* Finish adapting to OpenFisca-Core 17.0.0
  - One renaming had not been applied

## 6.2.1

* Adapt to OpenFisca-Core 17.0.0

## 6.2.0

* Enable API monitoring with Piwik
  - See the [documentation](https://github.com/openfisca/openfisca-web-api/#tracker)

# 6.0.0

* Remove deprecated route `/fields`
* Make route `/variables` compatible with OpenFisca-Core >= 14

## 5.1.0

* Make the API compatible with OpenFisca Core 12

## 5.0.1

* Technical change: return a nice error message to the user instead of a generic "Server Error".
    - Impacts `simulate` endpoint.

## 5.0.0

* Breaking change: Adapt Web-API to OpenFisca-Core 10

* Technical change: return the error message to the user instead of a generic "Server Error".
    - Impacts `calculate` and `simulate` endpoints.
    - In particular when a wrong period is specified for an input variable in the JSON payload

## 4.0.0

* Restrict the accepted formats to define a period
  - The valid formats are listed in [the doc](http://openfisca.org/doc/periodsinstants.html)

## 3.4.0

* Improve error messages when the test case is invalid
* Make the web API compatible with `OpenFisca-Core v8`

## 3.3.1

* Technical and not breaking change
  - Move JSON representation of entities to the Core for code factorization

## 3.3.0

* Adapt the web API to make it compatible with `OpenFisca-Core v7`

## 3.2.1

* Add documentation and example files to deploy in production.

## 3.2.0

* Make the script `openfisca-serve` work with any country
    - Before, it was always loading `openfisca-france`
    - Now, the country package (as well as reforms and extensions) can be provided through arguments
    - If no country package is provided, an auto-detection is attempted

For more information about how to use the script, run `openfisca-serve -h`.

## 3.1.1

* Bugfix: in development mode, fix the path of the country package. This impacts the `parameters` endpoint.

## 3.1.0

* Accept other countries than OpenFisca-France and OpenFisca-Tunisia.
* The endpoint `parameters` now removes the `description` key from the JSON response, instead of an empty string,
  when nodes of the legislation XML have no description.

## 3.0.2

* Fix the condition to detect if the country package has decompositions:
    * Load decompositions only if `tax_benefit_system` has a `decomposition_file_path` attribute.

## 3.0.1

* Rename variables to make the tests pass.
* Remove the dependency constraint to France.

## 3.0.0

* Adapt parsers to core#v4

* Breaking change:
    * Route /1/entities deprecated, replaced by /2/entities with different structure.

## 2.0.3

* Refactor middlewares in order to send error emails *and* returning JSON with correct content-type.

## 2.0.2

* Remove any mention to `conda` in README, since we use `pip` now.

## 2.0.1

* In some cases in `/variables` endpoint, `source_file_path` of each variable was wrong if application was deployed
  in a virtualenv. This fix uses `importlib` to get the path of the country package instead of `pkg_resources`.

## 2.0.0

* Update introspection data (via OpenFisca-Core update)
* Add country_package_name to parameters and variables endpoints
* Add debug logging to load_environment
* Do not pre-load 2 years in debug mode
* Add currency to variables endpoint

## 1.2.2

* Update travis procedures

## 1.2.1 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.2.0...1.2.1)

* Fix run-travis-tests.sh to repair automatic pypi releasing

## 1.2.0 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.1.0...1.2.0)

* Declare TBS extensions in configuration file

## 1.1.0 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.0.4...1.1.0)

* Add openfisca-serve CLI script to quickly launch the api with a basic conf

## 1.0.4 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.0.3...1.0.4)

* Update numpy dependency to 1.11

## 1.0.3 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.0.2...1.0.3)

* Apply core API changes introduced by openfisca-core 2.0

## 1.0.2 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.0.1...1.0.2)

* Force updating version number and CHANGELOG.md before merging on master
* Release tag and Pip version automatically

## 1.0.1 – [diff](https://github.com/openfisca/openfisca-web-api/compare/1.0.0...1.0.1)

* Use package version instead of git sha.

## 1.0.0 – [diff](https://github.com/openfisca/openfisca-web-api/compare/0.5.2...1.0.0)

* Switch to [semantic versioning](http://semver.org/)

## 0.5.2 – [diff](https://github.com/openfisca/openfisca-web-api/compare/0.5.1...0.5.2)

* Misc updates

## 0.5.1 – [diff](https://github.com/openfisca/openfisca-web-api/compare/0.5.0...0.5.1)

* Remove docs, move to openfisca-gitbook repo
* Update to travis new infrastructure
* Do not install scipy in travis

## 0.5.0

* First release uploaded to PyPI
