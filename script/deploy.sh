#!/bin/bash
set -ev -o pipefail

echo "Simulate deploying now..."
pwd
docker-compose -p beevenue down
sed -i 's/\(COMMIT_ID = \)\(.*\)/\1\"'${1:0:8}'\"/g' beevenue_config.py
docker-compose -p beevenue up --build -d