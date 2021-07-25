#!/bin/env sh

env BEEVENUE_CONFIG_FILE="test/testing_config.py" coverage run --branch --source=beevenue -m pytest --disable-pytest-warnings "$@" test
coverage report -m --skip-covered
coverage xml
coveralls