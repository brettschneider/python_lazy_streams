#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
rm -r .coverage 2> /dev/null
pytest --cov=. --junitxml=test_results.xml -v && coverage html && coverage xml
