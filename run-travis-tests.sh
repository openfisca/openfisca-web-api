#! /usr/bin/env bash

# This script is the entry point for the Travis tests platform.
# It allows Travis to checkout on OpenFisca-Core, OpenFisca-France and OpenFisca-Parsers
# the git branch with the same name than the tested branch,
# so that the pull-request merge status remains valid.


set -x

current_version=`python setup.py --version`
if [[ "$TRAVIS_BRANCH" == "master" && "$TRAVIS_PULL_REQUEST" != false ]]
then
    if git rev-parse $current_version
    then
        set +x
        echo "Version $version already exists. Please update version number in setup.py before merging this branch into master."
        exit 1
    fi

    if git diff-index master --quiet CHANGELOG.md
    then
        set +x
        echo "CHANGELOG.md has not been modified. Please update it before merging this branch into master."
        exit 1
    fi
fi

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


make test

bash openfisca_web_api/tests/test-cli.sh
