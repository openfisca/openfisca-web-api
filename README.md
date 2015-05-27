# OpenFisca Web-API

[![Build Status via Travis CI](https://travis-ci.org/openfisca/openfisca-web-api.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-web-api)

## Presentation

[OpenFisca](http://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Web-API module.

Please consult http://www.openfisca.fr/presentation

## Documentation

Please consult http://www.openfisca.fr/documentation

## Installation

An opened instance of the OpenFisca API is hosted online at http://api.openfisca.fr/.
You need to install this Python package if you want to contribute to its source code or run a local instance
on your computer.

Clone the OpenFisca-Web-API Git repository on your machine and install the Python package.
Assuming you are in your working directory:

```
git clone https://github.com/openfisca/openfisca-web-api.git
cd openfisca-web-api
pip install --editable .[dev] --user
python setup.py compile_catalog
```

Run the Python HTTP server:

    paster serve --reload development-france.ini

To stop the server, interrupt the command with Ctrl-C.

To check if it's OK, open the following URL in your browser:
http://localhost:2000/ (2000 is the port number defined in the development-france.ini config file).
You should see a JSON response telling that the path is not found (which is normal as no endpoint corresponds to "/"):

    {"apiVersion": "1.0", "error": {"message": "Path not found: /", "code": 404}}

## Docker containers

Docker containers are available:
[docker-france](https://github.com/openfisca/openfisca-web-api/tree/master/docker-france),
[docker-tunisia](https://github.com/openfisca/openfisca-web-api/tree/master/docker-tunisia) and
[docker-mes-aides](https://github.com/openfisca/openfisca-web-api/tree/master/docker-mes-aides).

## Contribute

OpenFisca is a free software project.
Its source code is distributed under the [GNU Affero General Public Licence](http://www.gnu.org/licenses/agpl.html)
version 3 or later (see COPYING).

Feel free to join the OpenFisca development team on [GitHub](https://github.com/openfisca) or contact us by email at
contact@openfisca.fr
