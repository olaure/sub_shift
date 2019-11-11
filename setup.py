#!/usr/bin/env python

from setuptools import setup

with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

requires = [
    'click'
]

setup(
    version='1.0',
    description='A very simple subtitle file time shifter',
    long_description=readme,
    author='olaure',
    author_email='',
    url='https://github.com/olaure/sub_shift',
    packages=['distutils', 'distutils.command'],
    requires=install_requirements,
)
