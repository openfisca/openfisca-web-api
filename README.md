# OpenFisca Web-API

[![Build Status](https://travis-ci.org/openfisca/openfisca-web-api.svg?branch=master)](https://travis-ci.org/openfisca/openfisca-web-api)

[More build status](http://www.openfisca.fr/build-status)

[OpenFisca](http://www.openfisca.fr/) is a versatile microsimulation free software.
This is the source code of the Web-API module.

Please consult http://doc.openfisca.fr/

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

Here we use Apache with mod_wsgi under Debian Jessie.

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

## Test

If you installed OpenFisca-Web-API from Git you can run the unit tests:

```
# go to the git cloned directory
cd /path/to/openfisca-web-api
make test
```

Also see [examples](./examples/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
