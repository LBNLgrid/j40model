# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='j40_model',
    version='0.1.0',
    description='Base simulation and optimization modules for J40 tool',
    long_description=readme,
    author='Miguel Heleno',
    author_email='miguelhelenoa@lbl.gov',
    include_package_data=True,
    packages=['j40_model'],
)
