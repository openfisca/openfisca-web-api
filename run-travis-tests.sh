#! /usr/bin/env bash

# This script is the entry point for the Travis tests platform.
# It allows Travis to checkout on OpenFisca-Core, OpenFisca-France and OpenFisca-Parsers
# the git branch with the same name than the tested branch,
# so that the pull-request merge status remains valid.


set -x


function checkout {
  name="$1"
  DIR=`python -c "import pkg_resources; print pkg_resources.get_distribution('$name').location"`
  pushd "$DIR"
  git checkout "$TRAVIS_BRANCH"
  popd
}


if [ "$TRAVIS_BRANCH" != "master" ]; then
  checkout "OpenFisca-Core"
  checkout "OpenFisca-France"
  checkout "OpenFisca-Parsers"
fi


# make test-ci
