#!/bin/sh

set -e

# Usage function
usage() {
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.1"
    exit 1
}

# Check if version is provided
if [ $# -eq 0 ]; then
    usage
fi

VERSION=$1

echo "🚀 Deploying version: $VERSION"

# Step 1: Build and push the image with version
echo "📦 Building and pushing Docker image..."
./docker-push-aws.sh $VERSION

# Step 2: Deploy with Terraform using the new version
echo "🏗️ Updating AWS infrastructure..."
cd tf
terraform apply -var="image_version=$VERSION" -auto-approve

echo "✅ Deployment complete! Version $VERSION is now running."
echo "🔍 Check service status with: aws ecs describe-services --cluster rfc7591-cluster --services rfc7591-service"