TESTS_DIR=openfisca_web_api/tests

all: flake8 test

clean: clean-pyc
	rm -rf build dist

clean-pyc:
	find . -name '*.pyc' -exec rm \{\} \;

ctags:
	ctags --recurse=yes --exclude=node_modules --exclude=openfisca_web_ui/static/dist .

flake8:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$"`

test: flake8
	nosetests $(TESTS_DIR) --exe --stop --with-doctest

test-ci: flake8
	nosetests $(TESTS_DIR) --exe --with-doctest

test-with-coverage:
	nosetests $(TESTS_DIR) --exe --stop --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html
