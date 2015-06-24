#! /usr/bin/env python
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


"""Web API for OpenFisca -- a versatile microsimulation free software"""


from setuptools import setup, find_packages


classifiers = """\
Development Status :: 2 - Pre-Alpha
Environment :: Web Environment
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: POSIX
Programming Language :: Python
Topic :: Scientific/Engineering :: Information Analysis
Topic :: Internet :: WWW/HTTP :: WSGI :: Server
"""

doc_lines = __doc__.split('\n')


setup(
    name = 'OpenFisca-Web-API',
    version = '0.5.dev0',

    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.fr',
    classifiers = [classifier for classifier in classifiers.split('\n') if classifier],
    description = doc_lines[0],
    keywords = 'api benefit microsimulation server social tax web',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    long_description = '\n'.join(doc_lines[2:]),
    url = 'https://github.com/openfisca/openfisca-web-api',

    data_files = [
        ('share/locale/fr/LC_MESSAGES', ['openfisca_web_api/i18n/fr/LC_MESSAGES/openfisca-web-api.mo']),
        ],
    entry_points = {
        'paste.app_factory': 'main = openfisca_web_api.application:make_app',
        },
    extras_require = {
        'dev': ['PasteScript'],
        'introspection': ['OpenFisca-Parsers >= 0.5dev'],
        },
    include_package_data = True,
    install_requires = [
        'Babel >= 0.9.4',
        'Biryani >= 0.10.4',
        'OpenFisca-Core >= 0.5dev',
        'WebError >= 0.10',
        'WebOb >= 1.1',
        ],
    message_extractors = {'openfisca_web_api': [
        ('**.py', 'python', None),
        ]},
    # package_data = {'openfisca_web_api': ['i18n/*/LC_MESSAGES/*.mo']},
    packages = find_packages(),
    test_suite = 'nose.collector',
    zip_safe = False,
    )
