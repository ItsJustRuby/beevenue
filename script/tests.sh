#!/bin/bash
set -ev -o pipefail

docker-compose -p beevenue-tests -f docker-compose.tests.yml build app tests
docker-compose -p beevenue-tests -f docker-compose.tests.yml run tests "$@"
