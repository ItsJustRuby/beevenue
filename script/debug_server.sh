#!/bin/env sh
env BEEVENUE_SKIP_SPINDEX=1 /bin/sh ./script/flask.sh db upgrade

env BEEVENUE_CONFIG_FILE=./beevenue_config.py python main.py