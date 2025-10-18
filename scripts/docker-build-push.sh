#!/bin/bash

# Docker build and push script for kim-secretary-api
# Usage: ./scripts/docker-build-push.sh [tag]
# Example: ./scripts/docker-build-push.sh v1.0.0

set -e

# Configuration
IMAGE_NAME="junho5336/kim-secretary-api"
DEFAULT_TAG="latest"
TAG="${1:-$DEFAULT_TAG}"

echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG}"

# Build the Docker image
docker build -t "${IMAGE_NAME}:${TAG}" .

# Also tag as latest if a specific version was provided
if [ "$TAG" != "latest" ]; then
    echo "🏷️  Tagging as latest"
    docker tag "${IMAGE_NAME}:${TAG}" "${IMAGE_NAME}:latest"
fi

echo "📤 Pushing Docker image to Docker Hub"

# Push the specified tag
docker push "${IMAGE_NAME}:${TAG}"

# Push latest if tagged
if [ "$TAG" != "latest" ]; then
    docker push "${IMAGE_NAME}:latest"
fi

echo "✅ Successfully pushed ${IMAGE_NAME}:${TAG}"
if [ "$TAG" != "latest" ]; then
    echo "✅ Successfully pushed ${IMAGE_NAME}:latest"
fi

echo ""
echo "🎉 Done! Your image is available at:"
echo "   docker pull ${IMAGE_NAME}:${TAG}"
if [ "$TAG" != "latest" ]; then
    echo "   docker pull ${IMAGE_NAME}:latest"
fi