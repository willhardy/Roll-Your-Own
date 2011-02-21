#!/usr/bin/env python
# -*- coding: UTF-8 -*-

try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup, find_packages
setup(
    name = "RollYourOwn",
    version = "1.0.0dev1",
    packages = find_packages(exclude=["docs*", "tests*", "examples*"]),
    namespace_packages = ["rollyourown"],
    install_requires = ['django>=1.0'],
    author = "Will Hardy",
    author_email = "rollyourown@hardysoftware.com.au",
    description = "A series frameworks to ease development of hand rolled django applications.",
    long_description = open('README.txt').read(),
    license = "LICENSE.txt",
    keywords = "ecommerce, django, framework",
    url = "http://rollyourown.hardysoftware.com.au/",

)

