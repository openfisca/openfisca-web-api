openfisca-serve &

wget --quiet --retry-connrefused --waitretry=1 --output-document=/dev/null http://localhost:2000
