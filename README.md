# OpenFisca new Web-API

## Install

```sh
git clone https://github.com/openfisca/openfisca-web-api.git
cd openfisca-web-api
git checkout rewrite
pip install -e ".[test]"
```

## Test

```sh
nosetests
```

## Run

```sh
COUNTRY_PACKAGE=openfisca_france FLASK_APP=openfisca_web_api/server.py flask run
```
