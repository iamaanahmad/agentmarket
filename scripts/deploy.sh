#!/bin/bash

# SecurityGuard AI Deployment Script
# Handles Docker build, push, and Kubernetes deployment

set -e

# Configuration
IMAGE_NAME="security-guard-ai"
IMAGE_TAG="${1:-latest}"
REGISTRY="${REGISTRY:-localhost:5000}"
NAMESPACE="${NAMESPACE:-default}"

echo "🚀 Starting SecurityGuard AI deployment..."
echo "Image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "Namespace: ${NAMESPACE}"

# Build Docker image
echo "📦 Building Docker image..."
cd security-ai
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Push to registry (if not localhost)
if [[ "${REGISTRY}" != "localhost:5000" ]]; then
    echo "📤 Pushing to registry..."
    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
fi

cd ..

# Apply Kubernetes configurations
echo "☸️ Deploying to Kubernetes..."

# Create namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets (make sure to update with real values)
echo "🔐 Applying secrets..."
kubectl apply -f k8s/secrets.yaml -n ${NAMESPACE}

# Apply deployment
echo "🚀 Applying deployment..."
sed "s|security-guard-ai:latest|${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml | kubectl apply -f - -n ${NAMESPACE}

# Apply HPA
echo "📈 Applying auto-scaling..."
kubectl apply -f k8s/hpa.yaml -n ${NAMESPACE}

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/security-guard-ai -n ${NAMESPACE} --timeout=300s

# Get service information
echo "✅ Deployment complete!"
echo ""
echo "Service Information:"
kubectl get services -n ${NAMESPACE} | grep security-guard-ai
echo ""
echo "Pod Status:"
kubectl get pods -n ${NAMESPACE} | grep security-guard-ai
echo ""
echo "HPA Status:"
kubectl get hpa -n ${NAMESPACE} | grep security-guard-ai

# Health check
echo ""
echo "🏥 Performing health check..."
SERVICE_IP=$(kubectl get service security-guard-ai-service -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
if kubectl run health-check --image=curlimages/curl --rm -i --restart=Never -- curl -f http://${SERVICE_IP}/health; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    exit 1
fi

echo ""
echo "🎉 SecurityGuard AI deployed successfully!"
echo "Monitor the deployment with: kubectl get pods -n ${NAMESPACE} -w"