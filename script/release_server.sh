#!/bin/env sh
# Run migrations (if necessary)
env BEEVENUE_SKIP_SPINDEX=1 /bin/sh ./script/flask.sh db upgrade

# Some requests may run longer than the default timout of 30s
env BEEVENUE_CONFIG_FILE=./beevenue_config.py gunicorn --workers 4 --timeout 90 -b 0.0.0.0:7000 main:app
