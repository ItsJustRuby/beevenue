#!/bin/env sh
env BEEVENUE_CONFIG_FILE="beevenue_config.py" FLASK_APP="main.py" flask "$@"
