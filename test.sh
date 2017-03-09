#!/bin/bash
clear
nosetests -v --with-coverage && coverage html
