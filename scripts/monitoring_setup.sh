#!/bin/bash

# SecurityGuard AI Monitoring Setup Script
# Sets up Prometheus, Grafana, and alerting

set -e

NAMESPACE="${NAMESPACE:-monitoring}"

echo "📊 Setting up SecurityGuard AI monitoring..."

# Create monitoring namespace
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
echo "🔍 Deploying Prometheus..."
cat <<EOF | kubectl apply -f - -n ${NAMESPACE}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--storage.tsdb.retention.time=200h'
        - '--web.enable-lifecycle'
      volumes:
      - name: config
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'security-guard-ai'
      static_configs:
      - targets: ['security-guard-ai-service.default.svc.cluster.local:80']
      metrics_path: '/metrics'
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
EOF

# Deploy Grafana
echo "📈 Deploying Grafana..."
cat <<EOF | kubectl apply -f - -n ${NAMESPACE}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"
        volumeMounts:
        - name: grafana-storage
          mountPath: /var/lib/grafana
      volumes:
      - name: grafana-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
EOF

# Wait for deployments
echo "⏳ Waiting for monitoring services to be ready..."
kubectl rollout status deployment/prometheus -n ${NAMESPACE} --timeout=300s
kubectl rollout status deployment/grafana -n ${NAMESPACE} --timeout=300s

# Get service information
echo "✅ Monitoring setup complete!"
echo ""
echo "Prometheus: http://$(kubectl get service prometheus -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}'):9090"
echo "Grafana: http://$(kubectl get service grafana -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):3000"
echo "Grafana credentials: admin/admin"
echo ""
echo "Import the SecurityGuard AI dashboard from monitoring/grafana/dashboards/security-guard-dashboard.json"