## Deploy OpenFisca-Web-API in production

> This how-to explains how to host OpenFisca-Web-API in *production*, for example to serve `api.xxx.com`.
> If you just need to develop with a local install of OpenFisca-Web-API, you need to read
> the main [README](https://github.com/openfisca/openfisca-web-api/blob/master/README.md).

The official and public instance of the API available at `https://api.openfisca.fr/` is hosted using:
- [Debian Jessie](https://www.debian.org/News/2015/20150426) GNU/Linux distribution
- [Nginx](https://www.nginx.com/) web server
- [gunicorn](http://gunicorn.org) WSGI-compatible Python web server

Here is the big picture:
- You should not clone this repository in order to host OpenFisca-Web-API, but use the Python package published to PyPI.
- Nginx serves content on the port 80, and proxyfies a subdomain to gunicorn.
- The application is installed in a Python virtualenv, managed with the shell-agnostic [pew](https://github.com/berdario/pew) tool.
- For the sake of the example we're going to host OpenFisca-France country.

```bash
sudo apt install nginx

# Now as normal user:
cd $HOME

pew new openfisca
# You should see "openfisca" in your shell prompt, which indicates the virtualenv is enabled.
# Next time, you'll use "pew workon openfisca" to enter.

# Upgrade some important Python packages:
pip install --upgrade pip wheel

pip install gunicorn OpenFisca-Web-API OpenFisca-France
```

Now that everything is installed, you must copy and adapt some config files from the production-config directory
(the one this README file is in) to your server.
Since you don't need to clone the current repository to install the Web API, you can copy the following files
using `scp` for example, or copy-paste their content.

- [`openfisca-web-api.conf`](./openfisca-web-api.conf) is the Nginx config for the virtual-host serving the API.
  It is already configured for SSL using [Let's Encrypt](https://letsencrypt.org/).
  Copy or link it to `/etc/nginx/sites-available/`, then do as root:
  ```bash
  ln -s /etc/nginx/sites-available/openfisca-web-api.conf /etc/nginx/sites-enabled/openfisca-web-api.conf`.
  ```
  Update the paths in the file.
  > It is inspired from the snippet shown in [Gunicorn deployment tutorial](http://gunicorn.org/#deployment).
- [`openfisca-web-api.service`](./openfisca-web-api.service) is the systemd service file which allows
to start the gunicorn server in the background.
  Copy or link it to `/etc/systemd/system`. Update the paths in the file.
- [`config.ini`](./config.ini) should be placed in your home directory or where you want.

Once the config are done, restart the services as root:

```bash
systemctl start openfisca-web-api
systemctl force-reload nginx
```

> The first time, systemctl can display a message inviting you to run a command to update itself: just follow the instructions.