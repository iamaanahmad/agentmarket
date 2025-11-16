#!/bin/bash

# SecurityGuard AI Production Deployment Script
# Comprehensive deployment with health checks, rollback capability, and monitoring

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="security-guard-ai"
IMAGE_TAG="${1:-$(date +%Y%m%d-%H%M%S)}"
REGISTRY="${REGISTRY:-ghcr.io/agentmarket}"
NAMESPACE="${NAMESPACE:-production}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Deployment failed. Initiating rollback..."
        rollback_deployment
    fi
}

trap cleanup EXIT

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if kubectl is available and configured
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
    
    # Check Docker/Podman availability
    if command -v docker &> /dev/null; then
        CONTAINER_CMD="docker"
    elif command -v podman &> /dev/null; then
        CONTAINER_CMD="podman"
    else
        log_error "Neither Docker nor Podman is available"
        exit 1
    fi
    
    # Check if required files exist
    local required_files=(
        "security-ai/Dockerfile"
        "k8s/deployment.yaml"
        "k8s/hpa.yaml"
        "k8s/secrets.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Pre-deployment checks passed"
}

# Build and push container image
build_and_push_image() {
    log_info "Building container image..."
    
    cd "$PROJECT_ROOT/security-ai"
    
    # Build image with multi-stage optimization
    $CONTAINER_CMD build \
        --tag "$IMAGE_NAME:$IMAGE_TAG" \
        --tag "$IMAGE_NAME:latest" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="$IMAGE_TAG" \
        .
    
    # Tag for registry
    $CONTAINER_CMD tag "$IMAGE_NAME:$IMAGE_TAG" "$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    $CONTAINER_CMD tag "$IMAGE_NAME:latest" "$REGISTRY/$IMAGE_NAME:latest"
    
    # Push to registry
    log_info "Pushing image to registry..."
    $CONTAINER_CMD push "$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    $CONTAINER_CMD push "$REGISTRY/$IMAGE_NAME:latest"
    
    cd "$PROJECT_ROOT"
    log_success "Image built and pushed: $REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
}

# Create backup before deployment
create_pre_deployment_backup() {
    log_info "Creating pre-deployment backup..."
    
    # Database backup
    if python3 "$PROJECT_ROOT/scripts/backup_restore.py" backup --type database; then
        log_success "Database backup completed"
    else
        log_warning "Database backup failed, continuing with deployment"
    fi
    
    # Configuration backup
    if python3 "$PROJECT_ROOT/scripts/backup_restore.py" backup --type config; then
        log_success "Configuration backup completed"
    else
        log_warning "Configuration backup failed, continuing with deployment"
    fi
}

# Deploy monitoring infrastructure
deploy_monitoring() {
    log_info "Deploying monitoring infrastructure..."
    
    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Prometheus and Grafana
    kubectl apply -f "$PROJECT_ROOT/k8s/monitoring.yaml" -n monitoring
    
    # Wait for monitoring to be ready
    kubectl rollout status deployment/prometheus -n monitoring --timeout=300s
    kubectl rollout status deployment/grafana -n monitoring --timeout=300s
    
    log_success "Monitoring infrastructure deployed"
}

# Deploy application
deploy_application() {
    log_info "Deploying SecurityGuard AI application..."
    
    # Store current deployment for rollback
    kubectl get deployment security-guard-ai -n "$NAMESPACE" -o yaml > /tmp/previous-deployment.yaml 2>/dev/null || true
    
    # Apply secrets (ensure they exist)
    kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml" -n "$NAMESPACE"
    
    # Update deployment with new image
    sed "s|security-guard-ai:latest|$REGISTRY/$IMAGE_NAME:$IMAGE_TAG|g" \
        "$PROJECT_ROOT/k8s/deployment.yaml" | \
        kubectl apply -f - -n "$NAMESPACE"
    
    # Apply HPA and other resources
    kubectl apply -f "$PROJECT_ROOT/k8s/hpa.yaml" -n "$NAMESPACE"
    kubectl apply -f "$PROJECT_ROOT/k8s/load-balancer.yaml" -n "$NAMESPACE"
    
    log_success "Application deployment manifests applied"
}

# Health checks and validation
perform_health_checks() {
    log_info "Performing health checks..."
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment rollout..."
    if ! kubectl rollout status deployment/security-guard-ai -n "$NAMESPACE" --timeout=600s; then
        log_error "Deployment rollout failed"
        return 1
    fi
    
    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=security-guard-ai -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
        local total_pods=$(kubectl get pods -n "$NAMESPACE" -l app=security-guard-ai --no-headers | wc -l)
        
        if [ "$ready_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
            log_success "All pods are ready ($ready_pods/$total_pods)"
            break
        fi
        
        log_info "Waiting for pods to be ready ($ready_pods/$total_pods)..."
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Pods failed to become ready within timeout"
        return 1
    fi
    
    # Health endpoint checks
    log_info "Checking application health endpoints..."
    local service_ip=$(kubectl get service security-guard-ai-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    # Test health endpoint
    if kubectl run health-check-$$-$RANDOM --image=curlimages/curl --rm -i --restart=Never -- \
        curl -f --max-time 10 "http://$service_ip/health"; then
        log_success "Health check endpoint is responding"
    else
        log_error "Health check endpoint failed"
        return 1
    fi
    
    # Test metrics endpoint
    if kubectl run metrics-check-$$-$RANDOM --image=curlimages/curl --rm -i --restart=Never -- \
        curl -f --max-time 10 "http://$service_ip/metrics"; then
        log_success "Metrics endpoint is responding"
    else
        log_warning "Metrics endpoint check failed"
    fi
    
    return 0
}

# Performance validation
validate_performance() {
    log_info "Validating application performance..."
    
    local service_ip=$(kubectl get service security-guard-ai-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    # Simple load test
    kubectl run load-test-$$-$RANDOM --image=curlimages/curl --rm -i --restart=Never -- \
        sh -c "
        for i in \$(seq 1 10); do
            start=\$(date +%s%N)
            if curl -f --max-time 5 -s http://$service_ip/health > /dev/null; then
                end=\$(date +%s%N)
                duration=\$(( (end - start) / 1000000 ))
                echo \"Request \$i: \${duration}ms\"
                if [ \$duration -gt 2000 ]; then
                    echo \"WARNING: Response time exceeded 2 seconds\"
                fi
            else
                echo \"Request \$i: FAILED\"
            fi
            sleep 1
        done
        "
    
    log_success "Performance validation completed"
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    if [ -f /tmp/previous-deployment.yaml ]; then
        kubectl apply -f /tmp/previous-deployment.yaml -n "$NAMESPACE"
        kubectl rollout status deployment/security-guard-ai -n "$NAMESPACE" --timeout=300s
        log_success "Rollback completed"
    else
        log_error "No previous deployment found for rollback"
        # Try to rollback to previous revision
        kubectl rollout undo deployment/security-guard-ai -n "$NAMESPACE"
        kubectl rollout status deployment/security-guard-ai -n "$NAMESPACE" --timeout=300s
        log_success "Rollback to previous revision completed"
    fi
}

# Post-deployment tasks
post_deployment_tasks() {
    log_info "Running post-deployment tasks..."
    
    # Update monitoring dashboards
    if kubectl get configmap grafana-dashboards -n monitoring &> /dev/null; then
        kubectl create configmap grafana-dashboards \
            --from-file="$PROJECT_ROOT/monitoring/grafana/dashboards/" \
            -n monitoring \
            --dry-run=client -o yaml | kubectl apply -f -
        log_success "Grafana dashboards updated"
    fi
    
    # Restart Grafana to pick up new dashboards
    kubectl rollout restart deployment/grafana -n monitoring || log_warning "Failed to restart Grafana"
    
    # Clean up old images (keep last 5)
    log_info "Cleaning up old container images..."
    $CONTAINER_CMD image prune -f || log_warning "Failed to prune images"
    
    # Update deployment annotations
    kubectl annotate deployment security-guard-ai -n "$NAMESPACE" \
        deployment.kubernetes.io/revision- \
        deployment.agentmarket.io/deployed-at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        deployment.agentmarket.io/deployed-by="$(whoami)" \
        deployment.agentmarket.io/image-tag="$IMAGE_TAG" \
        --overwrite
    
    log_success "Post-deployment tasks completed"
}

# Generate deployment report
generate_deployment_report() {
    log_info "Generating deployment report..."
    
    local report_file="/tmp/deployment-report-$IMAGE_TAG.txt"
    
    cat > "$report_file" << EOF
SecurityGuard AI Deployment Report
==================================

Deployment Details:
- Timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')
- Image Tag: $IMAGE_TAG
- Registry: $REGISTRY
- Namespace: $NAMESPACE
- Environment: $ENVIRONMENT

Deployment Status:
$(kubectl get deployment security-guard-ai -n "$NAMESPACE" -o wide)

Pod Status:
$(kubectl get pods -n "$NAMESPACE" -l app=security-guard-ai -o wide)

Service Status:
$(kubectl get services -n "$NAMESPACE" -l app=security-guard-ai -o wide)

HPA Status:
$(kubectl get hpa -n "$NAMESPACE" -l app=security-guard-ai -o wide)

Recent Events:
$(kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10)

Health Check Results:
- Application Health: $(kubectl run health-report-$$-$RANDOM --image=curlimages/curl --rm -i --restart=Never -- curl -f -s http://$(kubectl get service security-guard-ai-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')/health && echo "HEALTHY" || echo "UNHEALTHY")
- Metrics Endpoint: $(kubectl run metrics-report-$$-$RANDOM --image=curlimages/curl --rm -i --restart=Never -- curl -f -s http://$(kubectl get service security-guard-ai-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')/metrics > /dev/null && echo "AVAILABLE" || echo "UNAVAILABLE")

Resource Usage:
$(kubectl top pods -n "$NAMESPACE" -l app=security-guard-ai 2>/dev/null || echo "Metrics not available")

EOF

    log_success "Deployment report generated: $report_file"
    cat "$report_file"
}

# Main deployment flow
main() {
    log_info "Starting SecurityGuard AI production deployment..."
    log_info "Image Tag: $IMAGE_TAG"
    log_info "Registry: $REGISTRY"
    log_info "Namespace: $NAMESPACE"
    log_info "Environment: $ENVIRONMENT"
    
    # Execute deployment steps
    pre_deployment_checks
    create_pre_deployment_backup
    build_and_push_image
    deploy_monitoring
    deploy_application
    
    if perform_health_checks; then
        validate_performance
        post_deployment_tasks
        generate_deployment_report
        
        log_success "🎉 SecurityGuard AI deployment completed successfully!"
        log_info "Monitor the deployment with:"
        log_info "  kubectl get pods -n $NAMESPACE -w"
        log_info "  kubectl logs -f deployment/security-guard-ai -n $NAMESPACE"
        
        # Display service endpoints
        log_info "Service endpoints:"
        kubectl get services -n "$NAMESPACE" -l app=security-guard-ai
        
        # Display Grafana dashboard URL
        local grafana_ip=$(kubectl get service grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
        if [ "$grafana_ip" != "pending" ] && [ -n "$grafana_ip" ]; then
            log_info "Grafana Dashboard: http://$grafana_ip:3000"
        else
            log_info "Grafana Dashboard: kubectl port-forward -n monitoring service/grafana 3000:3000"
        fi
        
    else
        log_error "Health checks failed. Deployment unsuccessful."
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi