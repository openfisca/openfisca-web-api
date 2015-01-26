all: flake8 test

clean-pyc:
	find -name '*.pyc' -exec rm \{\} \;

ctags:
	ctags --recurse=yes --exclude=node_modules --exclude=openfisca_web_ui/static/dist .

flake8: clean-pyc
	flake8

test:
	nosetests -x --with-doctest openfisca_web_api/

test-with-coverage:
	nosetests -x --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html openfisca_web_api/
