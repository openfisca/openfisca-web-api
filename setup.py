#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name='OpenFisca-Web-API-Rewrite',
    version='0.1.0',
    author='OpenFisca Team',
    author_email='contact@openfisca.fr',
    description=u'OpenFisca Web API',
    license='https://www.gnu.org/licenses/agpl-3.0.html',
    url='https://github.com/openfisca/openfisca-web-api/tree/rewrite',
    extras_require={
        'test': [
            'Openfisca-Dummy-Country >= 0.1.1',
            'nose',
            'flake8',
            ],
        },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=[
        'flask == 0.12',
        'flask-cors == 3.0.2',
        'OpenFisca-Core >= 8.0.0, < 10.0',
        ],
    packages=find_packages(exclude=['openfisca_web_api.tests*']),
    test_suite='nose.collector',
    )
