# What is OpenFisca-Web-API-Tunisia?

[OpenFisca](http://www.openfisca.tn/) is a simulator for the tax-benefit systems of several countries.

[OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api) is the Git repository of the web API of OpenFisca. This web API can be configured to work for any country supported by OpenFisca.

OpenFisca-Web-API-Tunisia is the Docker image of this web API configured for [Tunisia](https://github.com/openfisca/openfisca-tunisia).


## Launch a local image of the tunisian web API

Update to the latest container version:

    docker pull openfisca/openfisca-web-api-tunisia:latest

Start the container in background:

    DOCKER_API_TUNISIA_ID=`docker run --detach -p 2001:2001 openfisca/openfisca-web-api-tunisia:latest`

Use the API, for example open this URL:

    http://localhost:2001/api/1/entities

Stop and remove the container when it's no more needed:

    docker stop $DOCKER_API_TUNISIA_ID
    docker rm $DOCKER_API_TUNISIA_ID
