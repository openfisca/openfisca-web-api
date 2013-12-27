.PHONY: flake8

flake8:
	rm -Rf cache/templates/
	flake8

