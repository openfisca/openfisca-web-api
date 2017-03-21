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
cd openfisca-web-api/openfisca_web_api
COUNTRY_PACKAGE=openfisca_dummy_country python server.py --port 6000
```
