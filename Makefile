TESTS_DIR="openfisca_web_api/tests/"

all: flake8 test

check-syntax-errors: clean-pyc
	@# This is a hack around flake8 not displaying E910 errors with the select option.
	test -z "`flake8 --first | grep E901`"

clean-pyc:
	find . -name '*.pyc' -exec rm \{\} \;

ctags:
	ctags --recurse=yes --exclude=node_modules --exclude=openfisca_web_ui/static/dist .

flake8: clean-pyc
	flake8

test: check-syntax-errors
	nosetests $(TESTS_DIR) --stop --with-doctest

test-with-coverage:
	nosetests $(TESTS_DIR) --stop --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
