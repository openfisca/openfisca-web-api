all: test

clean:
	rm -rf build dist
	find . -name '*.mo' -exec rm \{\} \;
	find . -name '*.pyc' -exec rm \{\} \;

apifr:
	paster serve --reload development-france.ini

apifr-with-tracking:
	paster serve --reload development-france.ini tracker_url=https://stats.data.gouv.fr/piwik.php tracker_idsite=4

flake8:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$"`

test: flake8
	nosetests openfisca_web_api --exe --with-doctest
	./openfisca_web_api/tests/test-cli.sh
