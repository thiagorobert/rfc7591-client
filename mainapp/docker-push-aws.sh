#!/bin/sh

set -e

# Get version from argument or default to latest
VERSION=${1:-latest}

LATEST_IMAGE=`docker images | awk '{ print $1; }' | grep rfc7591-test | head -1`
REPO="public.ecr.aws/f0b1x2x3/rfc7591-test"

echo "Pushing image with version: $VERSION"

# Login to ECR
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/f0b1x2x3

# Tag and push with version
docker tag $LATEST_IMAGE $REPO:$VERSION
docker push $REPO:$VERSION

# Also push as latest if version is not latest
if [ "$VERSION" != "latest" ]; then
  docker tag $LATEST_IMAGE $REPO:latest
  docker push $REPO:latest
fi

echo "Successfully pushed $REPO:$VERSION"
