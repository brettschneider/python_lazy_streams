#!/bin/bash

rm -fr build
rm -fr dist

python setup.py sdist bdist_wheel