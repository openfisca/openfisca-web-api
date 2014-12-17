check-tests-syntax:
	rm -Rf cache/templates/
	flake8 setup.py openfisca_web_api/

ctags:
	ctags --recurse=yes --exclude=node_modules --exclude=openfisca_web_ui/static/dist .

test: check-tests-syntax
	nosetests -x --with-doctest openfisca_web_api/

test-with-coverage:
	nosetests -x --with-coverage --cover-package=openfisca_core --cover-erase --cover-branches --cover-html openfisca_web_api/
