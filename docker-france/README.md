# What is OpenFisca-Web-API-France?

[OpenFisca](http://www.openfisca.fr/) is a simulator for the tax-benefit systems of several countries.

[OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api) is the Git repository of the web API of OpenFisca. This web API can be configured to work for any country supported by OpenFisca.

OpenFisca-Web-API-France is the Docker image of this web API configured for [France](https://github.com/openfisca/openfisca-france).


## Launch a local image of the french web API

Update to the latest container version:

    docker pull openfisca/openfisca-web-api-france:latest

Start the container in background:

    DOCKER_API_FRANCE_ID=`docker run --detach -p 2000:2000 openfisca/openfisca-web-api-france:latest`

Use the API, for example open this URL:

    http://localhost:2000/api/1/entities

Stop and remove the container when it's no more needed:

    docker stop $DOCKER_API_FRANCE_ID
    docker rm $DOCKER_API_FRANCE_ID
