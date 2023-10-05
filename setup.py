# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='j40model',
    version='1.1.0',
    description='Base simulation and optimization modules for J40 tool',
    long_description=readme,
    url='https://github.com/LBNLgrid/j40model',
    author='Miguel Heleno',
    author_email='miguelhelenoa@lbl.gov',
    include_package_data=True,
    install_requires=['geopandas==0.13',
                      'numpy==1.25',
                      'pandas==2.0',
                      'Pyomo==6.6']
)
