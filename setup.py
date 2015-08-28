#!/usr/bin/env python

import setuptools
from distutils.core import setup
import os
import versioneer
import archiver

__version__ = versioneer.get_versions(archiver.cfg, archiver.__file__)['version']

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='archiver',
    version=__version__,
    author='Brookhaven National Lab',
    url='http://github.com/ericdill/archiver',
    py_modules=['archiver'],
    license='BSD',
    )
