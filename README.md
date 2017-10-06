# OpenFisca Web-API - DEPRECATED

## This package is deprecated

**The official API is now available in [OpenFisca Core repository](https://github.com/openfisca/openfisca-core).**  
**The current package isn't maintained anymore: it won't evolve, and it is not guaranteed to be compatible with future versions of OpenFisca.**

The aim of this package was to provide OpenFisca information and computations through a web interface, without installing anything locally.

However, after a few years of existence, it appeared:
* That versioning OpenFisca API and the Core module apart was difficult to maintain
* That this API endpoints needed to be improved to match users experiences

## Introduction

[![Build Status](https://travis-ci.org/openfisca/openfisca-web-api.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-web-api) - [More build statuses](https://www.openfisca.fr/build-status)

[OpenFisca](https://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the deprecated Web-API module.

The documentation of the project is hosted at http://openfisca.org/doc/

## Local install

If you want to run the Web API on your machine, follow these steps.
Otherwise, read the documentation to learn how to [interact with `api.openfisca.fr`](http://openfisca.org/doc/openfisca-web-api/index.html).

Make sure you have Python 2 installed:

```sh
python --version
Python 2.7.9
```

Clone the repository:

```sh
git clone https://github.com/openfisca/openfisca-web-api.git
cd openfisca-web-api
```

Make sure you have the latest version of `pip`:

```sh
pip install --upgrade pip wheel
pip --version
# Should print at least 9.0 at the time we write this doc.
```

To avoid any dependencies problem we recommend you to use a [virtual environment](https://virtualenv.pypa.io/en/stable/),
for example with the tool : [pew](https://github.com/berdario/pew#command-reference).

```sh
sudo pip install pew
```

Now create a new virtual environment:

```sh
pew new openfisca --python=python2
# Answer "Y" to the question about modifying your shell config file.
# It creates a virtual environment named "openfisca".
# The virtualenv you just created will be automatically activated.
# Later, you'll just have to type "pew workon openfisca" to activate the virtualenv.
```

Now you have all the requirements to install OpenFisca in your virtual environment.

Install OpenFisca-Web-API (represented by `.` which is the current directory) and OpenFisca-France in your virtual env:

```sh
pip install --editable .[paster] OpenFisca-France
python setup.py compile_catalog
```

If no errors, the Web API is installed in your virtual env. You can now run it with the HTTP server.

## Run the HTTP server

```sh
paster serve --reload development-france.ini
```

To check if it's OK, open the following URL in your browser: http://localhost:2000/

> 2000 is the port number defined in the development-france.ini config file.

You should see this JSON response:

```json
{"apiVersion": 1, "message": "Welcome, this is OpenFisca Web API.", "method": "/"}
```

## Code architecture

Each API endpoint (`calculate`, `simulate`, etc.) source code has its own controller
(a function responding to a HTTP request) in `openfisca_web_api/controllers`.

Each controller function consists basically of 3 steps:
- reading and validating user input (with `req.params`)
- doing some computations
- returning the results in JSON (with `wsgihelpers.respond_json`)

The configuration of the application is stored in `development-<country>.ini` files, `<country>` being either
`france` or `tunisia`.
The configuration is validated once when the application starts.
The validation code is in `openfisca_web_api/environment.py` at the beginning of the `load_environment` function.

The tests are in `openfisca_web_api/tests`.

The function `make_app` in `openfisca_web_api/application.py` returns a [WSGI](http://wsgi.readthedocs.org/) application.
It is the main entry point of the application and is declared in `setup.py`.

All conversion and validation steps are done using the [Biryani](https://biryani.readthedocs.org) library.

## Test

If you installed OpenFisca-Web-API from Git you can run the unit tests:

```sh
make test
```

## Examples

See the [`examples` directory](./examples/).

## Deploy in production

See the [`production-config` directory](./production-config/).

## Tracker

The OpenFisca Web API comes with an [optional tracker](https://github.com/openfisca/tracker) which allows you to measure the usage of the API.

#### Tracker installation

The tracker is not installed by default. To install it, run:

```sh
pip install openfisca_web_api[tracker]  # Or `pip install --editable ".[tracker]"` for an editable installation
```


#### Tracker configuration

The tracker is activated when these two variables are set in the `.ini` configuration file:

* `tracker_url`: An URL ending with `piwik.php`. It defines the Piwik instance that will receive the tracking information.
* `tracker_idsite`: An integer. It defines the identifier of the tracked site on your Piwik instance.

For instance, to use the main OpenFisca piwik instance, add these lines to your configuration file:

```ini
tracker_url = https://stats.data.gouv.fr/piwik.php
tracker_idsite = 4
```
