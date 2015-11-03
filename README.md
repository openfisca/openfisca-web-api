# OpenFisca Web-API

[![Build Status](https://travis-ci.org/openfisca/openfisca-web-api.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-web-api)

[More build status](http://www.openfisca.fr/build-status)

[OpenFisca](http://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Web-API module.

Please consult http://doc.openfisca.fr/

## Install

Assuming you are in an `openfisca` working directory:

```
git clone https://github.com/openfisca/openfisca-web-api.git
cd openfisca-web-api
git checkout next
pip install --editable . --user # Microsoft Windows users must not use the `--user` option
python setup.py compile_catalog
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
