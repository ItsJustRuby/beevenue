#!/bin/bash
set -ev -o pipefail

# Run migrations (if necessary)
bash ./script/flask.sh db upgrade

bash ./script/flask.sh warmup

# Some requests may run longer than the default timout of 30s
BEEVENUE_CONFIG_FILE=./beevenue_config.py \
    gunicorn --workers 5 --timeout 90 -b 0.0.0.0:7000 \
    "$@" main:app
