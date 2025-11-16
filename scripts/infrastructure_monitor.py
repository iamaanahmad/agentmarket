#!/usr/bin/env python3
"""
Infrastructure Health Monitoring Script for SecurityGuard AI
Monitors system health, performance metrics, and alerts on issues
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import argparse

@dataclass
class HealthCheck:
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None

@dataclass
class InfrastructureStatus:
    overall_status: str
    checks: List[HealthCheck]
    timestamp: datetime
    summary: Dict[str, int]

class InfrastructureMonitor:
    def __init__(self, config_file: str = "monitoring_config.json"):
        self.config = self.load_config(config_file)
        self.session = None
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "kubernetes": {
                "namespace": "production",
                "deployment_name": "security-guard-ai"
            },
            "endpoints": {
                "health": "http://security-guard-ai-service/health",
                "metrics": "http://security-guard-ai-service/metrics",
                "prometheus": "http://prometheus:9090",
                "grafana": "http://grafana:3000"
            },
            "thresholds": {
                "response_time_ms": 2000,
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90,
                "error_rate": 0.05
            },
            "alerts": {
                "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
                "email_smtp": os.getenv("SMTP_SERVER"),
                "pagerduty_key": os.getenv("PAGERDUTY_KEY")
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
        
        return default_config
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def check_kubernetes_health(self) -> HealthCheck:
        """Check Kubernetes cluster and deployment health"""
        start_time = time.time()
        
        try:
            # Check if kubectl is available
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return HealthCheck(
                    name="kubernetes_cluster",
                    status="unhealthy",
                    response_time_ms=(time.time() - start_time) * 1000,
                    message="Kubernetes cluster not accessible",
                    timestamp=datetime.utcnow(),
                    details={"error": result.stderr}
                )
            
            # Check deployment status
            namespace = self.config["kubernetes"]["namespace"]
            deployment = self.config["kubernetes"]["deployment_name"]
            
            result = subprocess.run([
                "kubectl", "get", "deployment", deployment,
                "-n", namespace,
                "-o", "json"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return HealthCheck(
                    name="kubernetes_deployment",
                    status="unhealthy",
                    response_time_ms=(time.time() - start_time) * 1000,
                    message=f"Deployment {deployment} not found",
                    timestamp=datetime.utcnow(),
                    details={"error": result.stderr}
                )
            
            deployment_info = json.loads(result.stdout)
            status = deployment_info.get("status", {})
            
            ready_replicas = status.get("readyReplicas", 0)
            desired_replicas = status.get("replicas", 0)
            
            response_time = (time.time() - start_time) * 1000
            
            if ready_replicas == desired_replicas and ready_replicas > 0:
                return HealthCheck(
                    name="kubernetes_deployment",
                    status="healthy",
                    response_time_ms=response_time,
                    message=f"Deployment healthy: {ready_replicas}/{desired_replicas} replicas ready",
                    timestamp=datetime.utcnow(),
                    details={
                        "ready_replicas": ready_replicas,
                        "desired_replicas": desired_replicas,
                        "deployment_info": status
                    }
                )
            else:
                return HealthCheck(
                    name="kubernetes_deployment",
                    status="degraded" if ready_replicas > 0 else "unhealthy",
                    response_time_ms=response_time,
                    message=f"Deployment issues: {ready_replicas}/{desired_replicas} replicas ready",
                    timestamp=datetime.utcnow(),
                    details={
                        "ready_replicas": ready_replicas,
                        "desired_replicas": desired_replicas,
                        "deployment_info": status
                    }
                )
                
        except subprocess.TimeoutExpired:
            return HealthCheck(
                name="kubernetes_cluster",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message="Kubernetes command timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheck(
                name="kubernetes_cluster",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Kubernetes check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def check_application_health(self) -> HealthCheck:
        """Check application health endpoint"""
        start_time = time.time()
        
        try:
            # Use kubectl port-forward to access the service
            health_url = "http://localhost:8080/health"
            
            # Start port-forward in background
            port_forward = subprocess.Popen([
                "kubectl", "port-forward",
                f"service/{self.config['kubernetes']['deployment_name']}-service",
                "8080:80",
                "-n", self.config["kubernetes"]["namespace"]
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait a moment for port-forward to establish
            await asyncio.sleep(2)
            
            try:
                async with self.session.get(health_url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        health_data = await response.json()
                        
                        return HealthCheck(
                            name="application_health",
                            status="healthy",
                            response_time_ms=response_time,
                            message="Application health check passed",
                            timestamp=datetime.utcnow(),
                            details=health_data
                        )
                    else:
                        return HealthCheck(
                            name="application_health",
                            status="unhealthy",
                            response_time_ms=response_time,
                            message=f"Health check failed with status {response.status}",
                            timestamp=datetime.utcnow(),
                            details={"status_code": response.status}
                        )
            finally:
                port_forward.terminate()
                port_forward.wait()
                
        except asyncio.TimeoutError:
            return HealthCheck(
                name="application_health",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message="Health check timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheck(
                name="application_health",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def check_prometheus_metrics(self) -> HealthCheck:
        """Check Prometheus metrics and query performance"""
        start_time = time.time()
        
        try:
            # Use kubectl port-forward to access Prometheus
            prometheus_url = "http://localhost:9090"
            
            port_forward = subprocess.Popen([
                "kubectl", "port-forward",
                "service/prometheus",
                "9090:9090",
                "-n", "monitoring"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            await asyncio.sleep(2)
            
            try:
                # Query Prometheus for basic metrics
                query_url = f"{prometheus_url}/api/v1/query"
                params = {
                    "query": "up{job=\"security-guard-ai\"}"
                }
                
                async with self.session.get(query_url, params=params) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "success":
                            results = data.get("data", {}).get("result", [])
                            
                            if results:
                                return HealthCheck(
                                    name="prometheus_metrics",
                                    status="healthy",
                                    response_time_ms=response_time,
                                    message="Prometheus metrics available",
                                    timestamp=datetime.utcnow(),
                                    details={"metrics_count": len(results)}
                                )
                            else:
                                return HealthCheck(
                                    name="prometheus_metrics",
                                    status="degraded",
                                    response_time_ms=response_time,
                                    message="No metrics data available",
                                    timestamp=datetime.utcnow()
                                )
                        else:
                            return HealthCheck(
                                name="prometheus_metrics",
                                status="unhealthy",
                                response_time_ms=response_time,
                                message="Prometheus query failed",
                                timestamp=datetime.utcnow(),
                                details=data
                            )
                    else:
                        return HealthCheck(
                            name="prometheus_metrics",
                            status="unhealthy",
                            response_time_ms=response_time,
                            message=f"Prometheus not accessible: {response.status}",
                            timestamp=datetime.utcnow()
                        )
            finally:
                port_forward.terminate()
                port_forward.wait()
                
        except Exception as e:
            return HealthCheck(
                name="prometheus_metrics",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Prometheus check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def check_resource_usage(self) -> HealthCheck:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            # Get pod resource usage
            result = subprocess.run([
                "kubectl", "top", "pods",
                "-n", self.config["kubernetes"]["namespace"],
                "-l", f"app={self.config['kubernetes']['deployment_name']}",
                "--no-headers"
            ], capture_output=True, text=True, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            if result.returncode != 0:
                return HealthCheck(
                    name="resource_usage",
                    status="degraded",
                    response_time_ms=response_time,
                    message="Could not retrieve resource metrics",
                    timestamp=datetime.utcnow(),
                    details={"error": result.stderr}
                )
            
            # Parse resource usage
            lines = result.stdout.strip().split('\n')
            total_cpu = 0
            total_memory = 0
            pod_count = 0
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        cpu_str = parts[1].replace('m', '')
                        memory_str = parts[2].replace('Mi', '')
                        
                        try:
                            total_cpu += int(cpu_str)
                            total_memory += int(memory_str)
                            pod_count += 1
                        except ValueError:
                            continue
            
            # Determine status based on thresholds
            avg_cpu = total_cpu / pod_count if pod_count > 0 else 0
            avg_memory = total_memory / pod_count if pod_count > 0 else 0
            
            cpu_threshold = self.config["thresholds"]["cpu_percent"] * 10  # Convert to millicores
            memory_threshold = self.config["thresholds"]["memory_percent"] * 20  # Rough conversion
            
            if avg_cpu > cpu_threshold or avg_memory > memory_threshold:
                status = "degraded"
                message = f"High resource usage: CPU {avg_cpu}m, Memory {avg_memory}Mi"
            else:
                status = "healthy"
                message = f"Resource usage normal: CPU {avg_cpu}m, Memory {avg_memory}Mi"
            
            return HealthCheck(
                name="resource_usage",
                status=status,
                response_time_ms=response_time,
                message=message,
                timestamp=datetime.utcnow(),
                details={
                    "pod_count": pod_count,
                    "total_cpu_millicores": total_cpu,
                    "total_memory_mi": total_memory,
                    "avg_cpu_millicores": avg_cpu,
                    "avg_memory_mi": avg_memory
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="resource_usage",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Resource check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def check_database_connectivity(self) -> HealthCheck:
        """Check database connectivity through application"""
        start_time = time.time()
        
        try:
            # This would typically be done through the application's health endpoint
            # For now, we'll check if the database pods are running
            result = subprocess.run([
                "kubectl", "get", "pods",
                "-n", self.config["kubernetes"]["namespace"],
                "-l", "app=postgres",
                "-o", "json"
            ], capture_output=True, text=True, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            if result.returncode != 0:
                return HealthCheck(
                    name="database_connectivity",
                    status="unhealthy",
                    response_time_ms=response_time,
                    message="Could not check database status",
                    timestamp=datetime.utcnow(),
                    details={"error": result.stderr}
                )
            
            pods_info = json.loads(result.stdout)
            pods = pods_info.get("items", [])
            
            if not pods:
                return HealthCheck(
                    name="database_connectivity",
                    status="unhealthy",
                    response_time_ms=response_time,
                    message="No database pods found",
                    timestamp=datetime.utcnow()
                )
            
            running_pods = 0
            for pod in pods:
                status = pod.get("status", {})
                phase = status.get("phase", "")
                if phase == "Running":
                    running_pods += 1
            
            if running_pods == len(pods):
                return HealthCheck(
                    name="database_connectivity",
                    status="healthy",
                    response_time_ms=response_time,
                    message=f"Database healthy: {running_pods}/{len(pods)} pods running",
                    timestamp=datetime.utcnow(),
                    details={"running_pods": running_pods, "total_pods": len(pods)}
                )
            else:
                return HealthCheck(
                    name="database_connectivity",
                    status="degraded",
                    response_time_ms=response_time,
                    message=f"Database issues: {running_pods}/{len(pods)} pods running",
                    timestamp=datetime.utcnow(),
                    details={"running_pods": running_pods, "total_pods": len(pods)}
                )
                
        except Exception as e:
            return HealthCheck(
                name="database_connectivity",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Database check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def run_all_checks(self) -> InfrastructureStatus:
        """Run all health checks concurrently"""
        checks = await asyncio.gather(
            self.check_kubernetes_health(),
            self.check_application_health(),
            self.check_prometheus_metrics(),
            self.check_resource_usage(),
            self.check_database_connectivity(),
            return_exceptions=True
        )
        
        # Filter out exceptions and convert to HealthCheck objects
        valid_checks = []
        for check in checks:
            if isinstance(check, HealthCheck):
                valid_checks.append(check)
            elif isinstance(check, Exception):
                valid_checks.append(HealthCheck(
                    name="unknown_check",
                    status="unhealthy",
                    response_time_ms=0,
                    message=f"Check failed with exception: {str(check)}",
                    timestamp=datetime.utcnow(),
                    details={"exception": str(check)}
                ))
        
        # Calculate overall status
        status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}
        for check in valid_checks:
            status_counts[check.status] += 1
        
        if status_counts["unhealthy"] > 0:
            overall_status = "unhealthy"
        elif status_counts["degraded"] > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return InfrastructureStatus(
            overall_status=overall_status,
            checks=valid_checks,
            timestamp=datetime.utcnow(),
            summary=status_counts
        )
    
    async def send_alert(self, status: InfrastructureStatus):
        """Send alerts for unhealthy status"""
        if status.overall_status == "healthy":
            return
        
        alert_message = f"""
🚨 SecurityGuard AI Infrastructure Alert

Overall Status: {status.overall_status.upper()}
Timestamp: {status.timestamp.isoformat()}

Failed Checks:
"""
        
        for check in status.checks:
            if check.status != "healthy":
                alert_message += f"- {check.name}: {check.status} - {check.message}\n"
        
        alert_message += f"\nSummary: {status.summary}"
        
        # Send to Slack if configured
        slack_webhook = self.config["alerts"].get("slack_webhook")
        if slack_webhook:
            try:
                payload = {
                    "text": alert_message,
                    "username": "SecurityGuard AI Monitor",
                    "icon_emoji": ":warning:" if status.overall_status == "degraded" else ":rotating_light:"
                }
                
                async with self.session.post(slack_webhook, json=payload) as response:
                    if response.status == 200:
                        print("Alert sent to Slack successfully")
                    else:
                        print(f"Failed to send Slack alert: {response.status}")
            except Exception as e:
                print(f"Error sending Slack alert: {e}")
        
        # Print alert to console
        print(alert_message)
    
    def print_status_report(self, status: InfrastructureStatus):
        """Print detailed status report"""
        print(f"\n{'='*60}")
        print(f"SecurityGuard AI Infrastructure Status Report")
        print(f"{'='*60}")
        print(f"Overall Status: {status.overall_status.upper()}")
        print(f"Timestamp: {status.timestamp.isoformat()}")
        print(f"Summary: {status.summary}")
        print(f"\nDetailed Checks:")
        print(f"{'-'*60}")
        
        for check in status.checks:
            status_icon = "✅" if check.status == "healthy" else "⚠️" if check.status == "degraded" else "❌"
            print(f"{status_icon} {check.name:<25} {check.status:<10} {check.response_time_ms:>6.0f}ms")
            print(f"   {check.message}")
            if check.details:
                print(f"   Details: {json.dumps(check.details, indent=2)}")
            print()
    
    async def continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous monitoring with specified interval"""
        print(f"Starting continuous monitoring (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                status = await self.run_all_checks()
                self.print_status_report(status)
                
                # Send alerts if needed
                await self.send_alert(status)
                
                # Wait for next check
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

async def main():
    parser = argparse.ArgumentParser(description="SecurityGuard AI Infrastructure Monitor")
    parser.add_argument("--config", default="monitoring_config.json", help="Configuration file path")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    parser.add_argument("--output", choices=["console", "json"], default="console", help="Output format")
    
    args = parser.parse_args()
    
    monitor = InfrastructureMonitor(args.config)
    
    try:
        await monitor.initialize()
        
        if args.continuous:
            await monitor.continuous_monitoring(args.interval)
        else:
            # Single check
            status = await monitor.run_all_checks()
            
            if args.output == "json":
                print(json.dumps(asdict(status), indent=2, default=str))
            else:
                monitor.print_status_report(status)
            
            # Exit with error code if unhealthy
            if status.overall_status == "unhealthy":
                sys.exit(1)
            elif status.overall_status == "degraded":
                sys.exit(2)
    
    finally:
        await monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())