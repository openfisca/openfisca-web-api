## Deploy OpenFisca-Web-API in production

> This how-to explains how to host OpenFisca-Web-API in *production*, for example to serve `api.xxx.com`.
> If you just need to develop with a local install of OpenFisca-Web-API, you need to read
> the main [README](https://github.com/openfisca/openfisca-web-api/blob/master/README.md).

The following instructions assume you use the Debian Jessie GNU/Linux distribution and that Python 2.7 is installed.

Here is the big picture:
- Use OpenFisca-Web-API Python package published to PyPI; do not clone this git repository.
- [Nginx](https://www.nginx.com/) serves content on the port 80 via a virtual host, and proxyfies a subdomain to
  [gunicorn](http://gunicorn.org).
- The application is installed in a Python virtualenv.
  - We recommend using [pew](https://github.com/berdario/pew) because it's written in Python so it's shell agnostic.
- For the sake of the example we're going to make the Web API serve the OpenFisca-France country.

First, install Nginx.

If you use the Debian Jessie GNU/Linux distribution on your server, type as root:

```sh
apt install nginx
```

For any other OS please read the [Nginx documentation](https://www.nginx.com/resources/wiki/start/topics/tutorials/install/).
For macOS you could consider using [`homebrew-nginx`](https://github.com/Homebrew/homebrew-nginx).

```sh
# Upgrade some important Python packages:
pip install --upgrade pip wheel

pip install pew
```

As normal user:

```sh
cd $HOME

pew new openfisca
# You should see "openfisca" in your shell prompt as a prefix, which indicates the virtualenv is enabled.
# Next time, you'll use `pew workon openfisca` to enter the virtualenv.

# Again, upgrade some important Python packages (this time *in* the virtualenv):
pip install --upgrade pip wheel

pip install gunicorn OpenFisca-Web-API OpenFisca-France
```

Now that everything is installed, you must copy and adapt some config files from the `production-config` directory
to your server. You can get those files by cloning this git repository on your server, modify them then delete the
repository.

- [`openfisca-web-api.conf`](./openfisca-web-api.conf) is the Nginx config for the virtual-host serving the API.

  It is already configured for SSL using [Let's Encrypt](https://letsencrypt.org/) for serving over HTTPS.

  Copy or link it to `/etc/nginx/sites-available/`, then do as root:

  ```sh
  ln -s /etc/nginx/sites-available/openfisca-web-api.conf /etc/nginx/sites-enabled/openfisca-web-api.conf`.
  ```

  Update the paths in the file.

  > See also [Gunicorn deployment tutorial](http://gunicorn.org/#deployment).

- [`openfisca-web-api.service`](./openfisca-web-api.service) is the systemd service file starting the gunicorn server.

  Copy or link it to `/etc/systemd/system`. Update the paths in the file.

- [`config.ini`](./config.ini) should be copied in any sub-directory of your home directory
  (ex: `/home/openfisca/production-config/openfisca-web-api/config.ini`)

  Update the email addresses and paths in the file.

Once the config is done, restart the services as root:

```sh
systemctl start openfisca-web-api
systemctl reload nginx
```

> The first time, `systemctl` can display a message inviting you to run a command to update itself:
> just follow the instructions.
