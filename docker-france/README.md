# What is OpenFisca-Web-API-France?

[OpenFisca](http://www.openfisca.fr/) is a simulator for the tax-benefit systems of several countries.

[OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api) is the Git repository of the web API of OpenFisca. This web API can be configured to work for any country supported by OpenFisca.

OpenFisca-Web-API-France is the Docker image of this web API configured for France.


## Launch a local image of the french web API

```
docker pull openfisca/openfisca-web-api-france:latest
docker run --detach -p 2000:2000 --name api-france openfisca/openfisca-web-api-france:latest
```
