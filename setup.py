#! /usr/bin/env python

from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name="lazy_streams",
    py_modules=["lazy_streams"],
    version="0.5",
    description="Inspired by Java 8 streams, simple list processing",
    long_description=long_description,
    author="Steve Brettschneider",
    author_email="steve@bluehousefamily.com",
    url="https://github.com/brettschneider/python_lazy_streams",
    download_url="https://github.com/brettschneider/python_lazy_streams/archive/0.4.tar.gz",
    keywords=["lazy", "stream", "list", "processing", "java"],
    classifiers=[],
    install_requires=["promise-keeper"]
)
