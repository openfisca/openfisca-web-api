# -*- coding: utf-8 -*-


import os
import pkg_resources

from paste.deploy import loadapp


app = None
CONF_FILE_NAME = 'test.ini'
CONF_TRACKING_FILE_NAME = 'test_tracking.ini'


def get_or_load_app():
    global app
    if app is None:
        pkg_root_dir = pkg_resources.get_distribution('OpenFisca-Web-API').location
        conf_file_path = os.path.join(pkg_root_dir, CONF_FILE_NAME)
        app = loadapp(u'config:{}#main'.format(conf_file_path))
    return app


def get_or_load_tracked_app():
    global app
    if app is None:
        pkg_root_dir = pkg_resources.get_distribution('OpenFisca-Web-API').location
        conf_file_path = os.path.join(pkg_root_dir, CONF_TRACKING_FILE_NAME)
        app = loadapp(u'config:{}#main'.format(conf_file_path))
    return app
