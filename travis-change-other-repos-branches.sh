#! /usr/bin/env bash

# This script allows Travis to checkout on OpenFisca-Core, France and Parsers
# the git branch with the same name than the tested branch.
# We do that to allow the development of features which involve cross-repositories code modifications.


function checkout {
    name="$1"
    DIR=`python -c "import pkg_resources; print pkg_resources.get_distribution('$name').location"`
    pushd "$DIR"
    git checkout "$TRAVIS_BRANCH" && pip install --editable .
    popd
}


if [[ "$TRAVIS_BRANCH" != "master" && -z "$TRAVIS_TAG" ]]
then
    checkout "OpenFisca-Core"
    checkout "OpenFisca-France"
    checkout "OpenFisca-Parsers"
fi
