# What is OpenFisca-Web-API-Mes-Aides?

[OpenFisca](http://www.openfisca.fr/) is a simulator for the tax-benefit systems of several countries.

[OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api) is the Git repository of the web API of OpenFisca. This web API can be configured to work for any country supported by OpenFisca.

OpenFisca-Web-API-Mes-Aides is the Docker image of this web API configured for [mes-aides.gouv.fr](http://mes-aides.gouv.fr/).


## Launch a local image of the mes-aides.gouv.fr web API

Update to the latest container version:

    docker pull openfisca/openfisca-web-api-mes-aides:latest

Start the container in background:

    DOCKER_API_MES_AIDES_ID=`docker run --detach -p 2000:2000 openfisca/openfisca-web-api-mes-aides:latest`

Use the API, for example open this URL:

    http://localhost:2000/api/1/entities

Stop and remove the container when it's no more needed:

    docker stop $DOCKER_API_MES_AIDES_ID
    docker rm $DOCKER_API_MES_AIDES_ID
