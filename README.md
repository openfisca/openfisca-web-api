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
COUNTRY_PACKAGE=openfisca_france FLASK_APP=openfisca_web_api/server.py flask run --with-threads
```

The `--with-threads` is necessary to avoid [this issue](https://github.com/corydolphin/flask-cors/issues/147#issuecomment-289539799). Without it, AJAX requests from Chrome sometimes take more than 20s to process.
