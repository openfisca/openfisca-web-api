# -*- coding: utf-8 -*-

import os
import sys
import argparse
from logging.config import fileConfig
from wsgiref.simple_server import make_server

from paste.deploy import loadapp


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-p', '--port', action = 'store', default = 2000, help = "port to serve on")
    args = parser.parse_args()

    port = int(args.port)
    hostname = 'localhost'
    conf_file_path = os.path.join(sys.prefix, 'share', 'openfisca', 'openfisca-web-api', 'development-france.ini')

    # If openfisca_web_api has been installed with --editable
    if not os.path.isfile(conf_file_path):
        import pkg_resources
        api_sources_path = pkg_resources.get_distribution("openfisca_web_api").location
        conf_file_path = os.path.join(api_sources_path, 'development-france.ini')

    fileConfig(conf_file_path)
    application = loadapp('config:{}'.format(conf_file_path))
    httpd = make_server(hostname, port, application)
    print u'Serving on http://{}:{}/'.format(hostname, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    sys.exit(main())
