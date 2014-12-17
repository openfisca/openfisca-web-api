FROM debian:unstable
# MAINTAINER OpenFisca Team <contact@openfisca.fr>
RUN apt-get update && apt-get upgrade -y
RUN apt-get install --no-install-recommends -y git python-babel python-isodate python-numpy python-pastedeploy python-pip python-scipy python-tz python-weberror python-webob
RUN apt-get clean
RUN pip install -e git+https://github.com/openfisca/openfisca-core.git#egg=OpenFisca-Core
RUN pip install -e git+https://github.com/sgmap/openfisca-france.git#egg=OpenFisca-France
RUN pip install -e git+https://github.com/openfisca/openfisca-web-api.git#egg=OpenFisca-Web-API

RUN sed -e "s/host = 127.0.0.1/host = 0.0.0.0/" /src/openfisca-web-api/development-france.ini > /src/openfisca-web-api/development-local.ini
RUN apt-get install --no-install-recommends -y python-pastescript
CMD paster serve /src/openfisca-web-api/development-local.ini
EXPOSE 2000
