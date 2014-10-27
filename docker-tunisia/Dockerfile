FROM debian:unstable
# MAINTAINER OpenFisca Team <contact@openfisca.fr>
RUN apt-get update && apt-get upgrade -y
RUN apt-get install --no-install-recommends -y git python-babel python-isodate python-numpy python-pastedeploy python-pip python-scipy python-tz python-weberror python-webob
RUN apt-get clean
RUN pip install -e git+https://github.com/etalab/biryani.git@biryani1#egg=Biryani1
RUN pip install -e git+https://github.com/openfisca/openfisca-core.git#egg=OpenFisca-Core
RUN pip install -e git+https://github.com/openfisca/openfisca-tunisia.git#egg=OpenFisca-Tunisia
RUN pip install -e git+https://github.com/openfisca/openfisca-web-api.git#egg=OpenFisca-Web-API

RUN apt-get install --no-install-recommends -y python-pastescript
RUN sed -e "s/host = 127.0.0.1/host = 0.0.0.0/" -e "s/country_package = openfisca_france/country_package = openfisca_tunisia/" /src/openfisca-web-api/development-tunisia.ini > /src/openfisca-web-api/development-local.ini
CMD paster serve /src/openfisca-web-api/development-local.ini
EXPOSE 2001
