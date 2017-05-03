test:
	flake8
	nosetests tests --exe --with-doctest
