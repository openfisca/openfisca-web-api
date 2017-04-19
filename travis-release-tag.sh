#! /usr/bin/env bash

version=`python setup.py --version`
git tag $version
git push git@github.com:openfisca/openfisca-web-api.git --tags
