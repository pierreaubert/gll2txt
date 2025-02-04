#!/bin/sh

rm -f *~ .*~ */*~ */*/*~

rm -f *.log .coverage
rm -f GLL2TXT_Converted.spec

rm -fr build dist .ruff_cache .pytest_cache __pycache__
