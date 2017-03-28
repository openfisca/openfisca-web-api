# OpenFisca new Web-API

This is the new OpenFisca web API, available at https://api-test.openfisca.fr/ (beta version).

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
COUNTRY_PACKAGE=openfisca_france gunicorn "openfisca_web_api.app:create_app()" --bind localhost:5000 --workers 3
```

The `--workers k` (with `k >= 3`) option is necessary to avoid [this issue](http://stackoverflow.com/questions/11150343/slow-requests-on-local-flask-server). Without it, AJAX requests from Chrome sometimes take more than 20s to process.

## Deploy

```sh
ssh deploy-new-api@api-test.openfisca.fr
```
