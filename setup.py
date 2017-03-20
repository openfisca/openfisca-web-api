#! /usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name='OpenFisca-Web-API-Rewrite',
    version='0.1.0',
    author='OpenFisca Team',
    author_email='contact@openfisca.fr',
    description=u'POC of a new API for OpenFisca',
    license='http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    url='https://github.com/openfisca/openfisca-web-api/tree/rewrite',
    extras_require={
        'test': [
            'Openfisca-Dummy-Country >= 0.1.1',
            'nose',
            ],
        },
    include_package_data = True,  # Will read MANIFEST.in
    install_requires=[
        'flask == 0.12',
        'OpenFisca-Core >= 8.0.0, < 9.0',
        ],
    packages=find_packages(exclude=['openfisca_web_api.tests*']),
    test_suite='nose.collector',
    )
