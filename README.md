# OpenFisca new Web-API

## Install

Will work once [this PR](https://github.com/openfisca/openfisca-core/pull/475) is merged. Until then, you need to install `openfisca-core` locally from the branch `variable-not-found`.

```sh
git@github.com:openfisca/openfisca-web-api.git
git checkout flask
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
