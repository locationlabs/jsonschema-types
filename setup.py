#!/usr/bin/env python

from setuptools import setup, find_packages

__version__ = '0.1'

__build__ = ''

setup(name='jsonschematypes',
      version=__version__ + __build__,
      description='JSON Schema type generator',
      author='Location Labs',
      author_email='info@locationlabs.com',
      url='http://www.locationlabs.com',
      packages=find_packages(exclude=['*.tests']),
      setup_requires=[
          'nose>=1.0'
      ],
      install_requires=[
          'jsonschema>=2.4.0',
          'inflection>=0.3.1',
          'python-magic>=0.4.6',
      ],
      tests_require=[
          'coverage>=3.7.1',
          'PyHamcrest>=1.8.3',
      ],
      test_suite='jsonschematypes.tests',
      )
