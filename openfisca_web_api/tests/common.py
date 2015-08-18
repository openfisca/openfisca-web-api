# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import pkg_resources

from paste.deploy import loadapp


app = None
CONF_FILE_NAME = 'test.ini'


def get_or_load_app():
    global app
    if app is None:
        pkg_root_dir = pkg_resources.get_distribution('OpenFisca-Web-API').location
        conf_file_path = os.path.join(pkg_root_dir, CONF_FILE_NAME)
        app = loadapp(u'config:{}#main'.format(conf_file_path))
    return app
