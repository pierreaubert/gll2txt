#!/bin/sh

rm -f *~ .*~ */*~ */*/*~
rm -f *.log .coverage
rm -fr build dist .ruff_cache .pytest_cache __pycache__
