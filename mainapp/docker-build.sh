#!/bin/sh

set -e

docker build "$@" . -t rfc7591-test-v`date +"%Y%m%d%H%M%S"`
