#!/bin/sh

set -e

LATEST=${1:-`docker images | awk '{ print $1; }' | grep rfc7591-test | head -1`}

echo "Running $LATEST"

docker run --env-file ../.env -p 3000:3000 -ti --rm $LATEST
