#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name = 'OpenFisca-Web-API',
    version = '3.0.1',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.fr',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        ],
    description = u'Web API for OpenFisca',
    keywords = 'api benefit microsimulation server social tax web',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url = 'https://github.com/openfisca/openfisca-web-api',

    data_files = [
        ('share/locale/fr/LC_MESSAGES', ['openfisca_web_api/i18n/fr/LC_MESSAGES/openfisca-web-api.mo']),
        (
            'share/openfisca/openfisca-web-api', [
                'CHANGELOG.md',
                'development-france.ini',
                'development-tunisia.ini',
                'LICENSE',
                'README.md',
                'test.ini',
                ],
            ),
        ],
    entry_points = {
        'console_scripts': ['openfisca-serve=openfisca_web_api.scripts.serve:main'],
        'paste.app_factory': 'main = openfisca_web_api.application:make_app',
        },
    extras_require = {
        'paster': [
            'PasteScript',
            ],
        'france': [
            'OpenFisca-France >= 5.0.0, < 7.0',
            ],
        'test': [
            'nose',
            ],
        },
    install_requires = [
        'Babel >= 0.9.4',
        'Biryani[datetimeconv] >= 0.10.4',
        'numpy >= 1.11',
        'OpenFisca-Core >= 4.0.0b1, < 5.0',
        'OpenFisca-Parsers >= 1.0.0, < 2.0',
        'PasteDeploy',
        'WebError >= 0.10',
        'WebOb >= 1.1',
        ],
    message_extractors = {'openfisca_web_api': [
        ('**.py', 'python', None),
        ]},
    packages = find_packages(exclude=['openfisca_web_api.tests*']),
    test_suite = 'nose.collector',
    )
