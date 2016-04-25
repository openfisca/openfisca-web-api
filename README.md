# OpenFisca Web-API

[![Build Status](https://travis-ci.org/openfisca/openfisca-web-api.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-web-api)

[More build statuses](http://www.openfisca.fr/build-status)

[OpenFisca](http://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Web-API module.

The documentation of the project is hosted at http://doc.openfisca.fr/

## Install to develop

Assuming you are in an `openfisca` working directory:

```
git clone https://github.com/openfisca/openfisca-web-api.git
cd openfisca-web-api
git checkout next
pip install --editable . --user # Microsoft Windows users must not use the `--user` option
python setup.py compile_catalog
```

## Deploy in production

Here we use Apache with `mod_wsgi` under Debian Jessie.

```
# aptitude install apache2 libapache2-mod-wsgi
```

Then create a vhost, for example (adapt to your domain name and paths):

```
WSGIDaemonProcess api.openfisca.fr display-name=api

<VirtualHost *:80>
    ServerName api.openfisca.fr
    ServerAdmin webmaster+api@openfisca.fr

    ErrorLog /var/log/apache2/api.openfisca.fr.error.log
    # NCSA extended/combined log format.
    LogFormat "%V %{X-Forwarded-For}i %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
    TransferLog /var/log/apache2/api.openfisca.fr.access.log
    # Possible values include: debug, info, notice, warn, error, crit, alert, emerg.
    LogLevel notice

    # Required to avoid an infinite loop when calling any API URL without importing Pandas.
    # Seems to be a numpy or scipy related bug.
    # Without this line, we get a "Premature end of script headers: application.py" error.
    WSGIApplicationGroup %{GLOBAL}
    WSGIProcessGroup api.openfisca.fr
    WSGIScriptAlias / /home/openfisca/vhosts/api.openfisca.fr/config/application.py

    Alias /robots.txt /home/openfisca/vhosts/api.openfisca.fr/static/robots.txt
</VirtualHost>
```

```
# ln -s /path/to/apache2.conf /etc/apache2/sites-available/api.openfisca.fr.conf
# a2ensite api.openfisca.fr.conf
# service apache2 force-reload
```

## Code architecture

Each API endpoint (`calculate`, `simulate`, etc.) source code has its own controller
(a function responding to a HTTP request) in `openfisca_web_api/controllers`.

Each controller function consists basically of 3 steps:
- reading and validating user input (with `req.params`)
- doing some computations
- returning the results in JSON (with `wsgihelpers.respond_json`)

The configuration of the application is stored in `development-<country>.ini` files, `<country>` being either
`france` or `tunisia`.
The configuration is validated once when the application starts.
The validation code is in `openfisca_web_api/environment.py` at the beginning of the `load_environment` function.

The tests are in `openfisca_web_api/tests`.

The function `make_app` in `openfisca_web_api/application.py` returns a [WSGI](http://wsgi.readthedocs.org/) application.
It is the main entry point of the application and is declared in `setup.py`.

All conversion and validation steps are done using the [Biryani](https://biryani.readthedocs.org) library.

## Test

If you installed OpenFisca-Web-API from Git you can run the unit tests:

```
# go to the git cloned directory
cd /path/to/openfisca-web-api
make test
```

Also see [examples](./examples/).
