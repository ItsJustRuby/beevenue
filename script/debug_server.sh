#!/bin/env sh
env /bin/sh ./script/flask.sh db upgrade

env BEEVENUE_CONFIG_FILE=./beevenue_config.py python main.py