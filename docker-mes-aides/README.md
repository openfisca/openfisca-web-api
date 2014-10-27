# What is OpenFisca-Web-API-Mes-Aides?

[OpenFisca](http://www.openfisca.fr/) is a simulator for the tax-benefit systems of several countries.

[OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api) is the Git repository of the web API of OpenFisca. This web API can be configured to work for any country supported by OpenFisca.

OpenFisca-Web-API-Mes-Aides is the Docker image of this web API configured for [mes-aides.gouv.fr](http://mes-aides.gouv.fr/).


## Launch a local image of the mes-aides.gouv.fr web API

```
docker run -d -p 2000:2000 openfisca/openfisca-web-api-mes-aides:latest
```

or

```
docker run -d -p 2000:2000 openfisca/openfisca-web-api-mes-aides:latest paster serve /src/openfisca-web-api/development-local.ini
```
