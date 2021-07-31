#!/bin/env sh

# Run migrations (if necessary)
env /bin/sh ./script/flask.sh db upgrade

env /bin/sh ./script/flask.sh warmup

# Some requests may run longer than the default timout of 30s
env BEEVENUE_CONFIG_FILE=./beevenue_config.py gunicorn --workers 4 --timeout 90 -b 0.0.0.0:7000 "$@" main:app
