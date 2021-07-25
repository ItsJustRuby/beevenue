#!/bin/sh
docker-compose -p beevenue -f docker-compose.yml -f docker-compose.debug.yml up --build "$@" -d 