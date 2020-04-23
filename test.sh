#!/bin/bash
clear
mypy --ignore-missing .
coverage run -m pytest tests.py
coverage html
