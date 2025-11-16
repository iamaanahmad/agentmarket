#!/usr/bin/env python3
"""
Disaster Recovery Automation for SecurityGuard AI
Handles automated failover, backup restoration, and system recovery
"""

import asyncio
import subprocess
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse
import boto3
from pathlib import Path

@dataclass
class RecoveryStep:
    name: str
    description: str
    command: List[str]
    timeout_seconds: int = 300
    critical: bool = True
    rollback_command: Optional[List[str]] = None

@dataclass
class RecoveryPlan:
    name: str
    description: str
    steps: List[RecoveryStep]
    estimated_time_minutes: int

class DisasterRecoveryManager:
    def __init__(self, config_file: str = "dr_config.json"):
        self.config = self.load_config(config_file)
        self.recovery_log = []
        self.start_time = None
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load disaster recovery configuration"""
        default_config = {
            "environments": {
                "production": {
                    "namespace": "production",
                    "region": "us-east-1",
                    "backup_bucket": "securityguard-backups-prod"
                },
                "staging": {
                    "namespace": "staging", 
                    "region": "us-east-1",
                    "backup_bucket": "securityguard-backups-staging"
                }
            },
            "recovery_plans": {
                "database_failure": {
                    "priority": 1,
                    "max_downtime_minutes": 15
                },
                "application_failure": {
                    "priority": 2,
                    "max_downtime_minutes": 5
                },
                "complete_failure": {
                    "priority": 1,
                    "max_downtime_minutes": 30
                }
            },
            "notifications": {
                "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
                "pagerduty_key": os.getenv("PAGERDUTY_KEY"),
                "email_recipients": ["oncall@securityguard.ai"]
            },
            "aws": {
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "region": "us-east-1"
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
    
    def log_step(self, step_name: str, status: str, message: str, details: Dict = None):
        """Log recovery step"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.recovery_log.append(log_entry)
        
        status_icon = "✅" if status == "success" else "❌" if status == "failed" else "⏳"
        print(f"{status_icon} [{datetime.utcnow().strftime('%H:%M:%S')}] {step_name}: {message}")
    
    async def execute_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Execute shell command with timeout"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "success": process.returncode == 0
            }
            
        except asyncio.TimeoutError:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timeout",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def get_database_recovery_plan(self, environment: str) -> RecoveryPlan:
        """Get database recovery plan"""
        env_config = self.config["environments"][environment]
        
        steps = [
            RecoveryStep(
                name="assess_database_damage",
                description="Assess database status and determine recovery approach",
                command=["kubectl", "get", "pods", "-n", env_config["namespace"], "-l", "app=postgres"],
                timeout_seconds=30
            ),
            RecoveryStep(
                name="stop_application_traffic",
                description="Stop application pods to prevent data corruption",
                command=["kubectl", "scale", "deployment", "security-guard-ai", "--replicas=0", "-n", env_config["namespace"]],
                timeout_seconds=60,
                rollback_command=["kubectl", "scale", "deployment", "security-guard-ai", "--replicas=3", "-n", env_config["namespace"]]
            ),
            RecoveryStep(
                name="backup_current_state",
                description="Create backup of current database state if possible",
                command=["python3", "scripts/backup_restore.py", "backup", "--type", "database"],
                timeout_seconds=300,
                critical=False
            ),
            RecoveryStep(
                name="download_latest_backup",
                description="Download latest database backup from S3",
                command=["aws", "s3", "cp", f"s3://{env_config['backup_bucket']}/database/", "./recovery/", "--recursive"],
                timeout_seconds=600
            ),
            RecoveryStep(
                name="restore_database",
                description="Restore database from backup",
                command=["python3", "scripts/backup_restore.py", "restore", "--file", "./recovery/latest_backup.sql.gz"],
                timeout_seconds=900
            ),
            RecoveryStep(
                name="verify_database_integrity",
                description="Verify database integrity and connectivity",
                command=["kubectl", "exec", "-n", env_config["namespace"], "deployment/postgres", "--", "psql", "-c", "SELECT 1;"],
                timeout_seconds=60
            ),
            RecoveryStep(
                name="restart_application",
                description="Restart application with restored database",
                command=["kubectl", "scale", "deployment", "security-guard-ai", "--replicas=3", "-n", env_config["namespace"]],
                timeout_seconds=120
            ),
            RecoveryStep(
                name="verify_application_health",
                description="Verify application health after recovery",
                command=["python3", "scripts/infrastructure_monitor.py", "--output", "json"],
                timeout_seconds=180
            )
        ]
        
        return RecoveryPlan(
            name="database_recovery",
            description="Recover from database failure using latest backup",
            steps=steps,
            estimated_time_minutes=25
        )
    
    def get_application_recovery_plan(self, environment: str) -> RecoveryPlan:
        """Get application recovery plan"""
        env_config = self.config["environments"][environment]
        
        steps = [
            RecoveryStep(
                name="assess_application_status",
                description="Check application pod status and errors",
                command=["kubectl", "get", "pods", "-n", env_config["namespace"], "-l", "app=security-guard-ai"],
                timeout_seconds=30
            ),
            RecoveryStep(
                name="collect_logs",
                description="Collect application logs for analysis",
                command=["kubectl", "logs", "-n", env_config["namespace"], "deployment/security-guard-ai", "--tail=100"],
                timeout_seconds=60,
                critical=False
            ),
            RecoveryStep(
                name="restart_application_pods",
                description="Restart application pods",
                command=["kubectl", "rollout", "restart", "deployment/security-guard-ai", "-n", env_config["namespace"]],
                timeout_seconds=180
            ),
            RecoveryStep(
                name="wait_for_rollout",
                description="Wait for deployment rollout to complete",
                command=["kubectl", "rollout", "status", "deployment/security-guard-ai", "-n", env_config["namespace"], "--timeout=300s"],
                timeout_seconds=320
            ),
            RecoveryStep(
                name="verify_pod_health",
                description="Verify all pods are healthy",
                command=["kubectl", "get", "pods", "-n", env_config["namespace"], "-l", "app=security-guard-ai"],
                timeout_seconds=60
            ),
            RecoveryStep(
                name="run_health_checks",
                description="Run comprehensive health checks",
                command=["python3", "scripts/infrastructure_monitor.py"],
                timeout_seconds=120
            )
        ]
        
        return RecoveryPlan(
            name="application_recovery",
            description="Recover from application failure by restarting pods",
            steps=steps,
            estimated_time_minutes=10
        )
    
    def get_complete_recovery_plan(self, environment: str) -> RecoveryPlan:
        """Get complete system recovery plan"""
        env_config = self.config["environments"][environment]
        
        steps = [
            RecoveryStep(
                name="assess_cluster_status",
                description="Check Kubernetes cluster status",
                command=["kubectl", "cluster-info"],
                timeout_seconds=30
            ),
            RecoveryStep(
                name="create_recovery_namespace",
                description="Ensure recovery namespace exists",
                command=["kubectl", "create", "namespace", f"{env_config['namespace']}-recovery", "--dry-run=client", "-o", "yaml"],
                timeout_seconds=30,
                critical=False
            ),
            RecoveryStep(
                name="download_all_backups",
                description="Download all available backups",
                command=["aws", "s3", "sync", f"s3://{env_config['backup_bucket']}/", "./recovery/"],
                timeout_seconds=900
            ),
            RecoveryStep(
                name="deploy_database",
                description="Deploy database from backup",
                command=["kubectl", "apply", "-f", "k8s/postgres.yaml", "-n", env_config["namespace"]],
                timeout_seconds=300
            ),
            RecoveryStep(
                name="restore_database_data",
                description="Restore database data from backup",
                command=["python3", "scripts/backup_restore.py", "restore", "--file", "./recovery/database/latest_backup.sql.gz"],
                timeout_seconds=1200
            ),
            RecoveryStep(
                name="deploy_redis",
                description="Deploy Redis cache",
                command=["kubectl", "apply", "-f", "k8s/redis.yaml", "-n", env_config["namespace"]],
                timeout_seconds=180
            ),
            RecoveryStep(
                name="deploy_application",
                description="Deploy SecurityGuard AI application",
                command=["kubectl", "apply", "-f", "k8s/deployment.yaml", "-n", env_config["namespace"]],
                timeout_seconds=300
            ),
            RecoveryStep(
                name="deploy_services",
                description="Deploy services and ingress",
                command=["kubectl", "apply", "-f", "k8s/load-balancer.yaml", "-n", env_config["namespace"]],
                timeout_seconds=120
            ),
            RecoveryStep(
                name="deploy_monitoring",
                description="Deploy monitoring infrastructure",
                command=["kubectl", "apply", "-f", "k8s/monitoring.yaml", "-n", "monitoring"],
                timeout_seconds=300
            ),
            RecoveryStep(
                name="wait_for_all_deployments",
                description="Wait for all deployments to be ready",
                command=["kubectl", "wait", "--for=condition=available", "--timeout=600s", "deployment", "--all", "-n", env_config["namespace"]],
                timeout_seconds=620
            ),
            RecoveryStep(
                name="verify_complete_system",
                description="Verify complete system health",
                command=["python3", "scripts/infrastructure_monitor.py"],
                timeout_seconds=180
            ),
            RecoveryStep(
                name="run_smoke_tests",
                description="Run smoke tests to verify functionality",
                command=["python3", "scripts/smoke_tests.py"],
                timeout_seconds=300,
                critical=False
            )
        ]
        
        return RecoveryPlan(
            name="complete_recovery",
            description="Complete system recovery from catastrophic failure",
            steps=steps,
            estimated_time_minutes=45
        )
    
    async def execute_recovery_plan(self, plan: RecoveryPlan) -> bool:
        """Execute a recovery plan"""
        self.start_time = datetime.utcnow()
        
        print(f"\n🚨 Starting Disaster Recovery: {plan.name}")
        print(f"Description: {plan.description}")
        print(f"Estimated time: {plan.estimated_time_minutes} minutes")
        print(f"Steps: {len(plan.steps)}")
        print("="*60)
        
        successful_steps = []
        failed_steps = []
        
        for i, step in enumerate(plan.steps, 1):
            print(f"\n[{i}/{len(plan.steps)}] {step.name}")
            print(f"Description: {step.description}")
            
            self.log_step(step.name, "running", f"Executing: {' '.join(step.command)}")
            
            result = await self.execute_command(step.command, step.timeout_seconds)
            
            if result["success"]:
                self.log_step(step.name, "success", "Step completed successfully", {
                    "stdout": result["stdout"][:500],  # Truncate long output
                    "execution_time": step.timeout_seconds
                })
                successful_steps.append(step)
            else:
                error_msg = f"Step failed: {result['stderr']}"
                self.log_step(step.name, "failed", error_msg, {
                    "returncode": result["returncode"],
                    "stderr": result["stderr"],
                    "stdout": result["stdout"]
                })
                failed_steps.append(step)
                
                if step.critical:
                    print(f"\n❌ Critical step failed: {step.name}")
                    print(f"Error: {result['stderr']}")
                    
                    # Attempt rollback if available
                    if step.rollback_command:
                        print(f"Attempting rollback...")
                        rollback_result = await self.execute_command(step.rollback_command, 60)
                        if rollback_result["success"]:
                            print("✅ Rollback successful")
                        else:
                            print(f"❌ Rollback failed: {rollback_result['stderr']}")
                    
                    return False
                else:
                    print(f"⚠️ Non-critical step failed, continuing: {step.name}")
        
        # Recovery completed
        end_time = datetime.utcnow()
        duration = end_time - self.start_time
        
        print(f"\n{'='*60}")
        print(f"🎉 Recovery Plan Completed: {plan.name}")
        print(f"Duration: {duration.total_seconds():.1f} seconds")
        print(f"Successful steps: {len(successful_steps)}/{len(plan.steps)}")
        
        if failed_steps:
            print(f"Failed steps: {len(failed_steps)}")
            for step in failed_steps:
                print(f"  - {step.name}")
        
        return len(failed_steps) == 0
    
    async def send_recovery_notification(self, plan_name: str, success: bool, duration_seconds: float):
        """Send recovery completion notification"""
        status_emoji = "✅" if success else "❌"
        status_text = "COMPLETED" if success else "FAILED"
        
        message = f"""
{status_emoji} Disaster Recovery {status_text}

Plan: {plan_name}
Duration: {duration_seconds:.1f} seconds
Timestamp: {datetime.utcnow().isoformat()}

Recovery Log:
"""
        
        # Add last few log entries
        for entry in self.recovery_log[-5:]:
            message += f"- {entry['step']}: {entry['status']} - {entry['message']}\n"
        
        # Send to Slack if configured
        slack_webhook = self.config["notifications"].get("slack_webhook")
        if slack_webhook:
            try:
                import aiohttp
                payload = {
                    "text": message,
                    "username": "SecurityGuard AI DR",
                    "icon_emoji": ":rotating_light:"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(slack_webhook, json=payload) as response:
                        if response.status == 200:
                            print("Recovery notification sent to Slack")
                        else:
                            print(f"Failed to send Slack notification: {response.status}")
            except Exception as e:
                print(f"Error sending Slack notification: {e}")
        
        print(message)
    
    def save_recovery_log(self, filename: Optional[str] = None):
        """Save recovery log to file"""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"recovery_log_{timestamp}.json"
        
        log_data = {
            "recovery_session": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": datetime.utcnow().isoformat(),
                "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
            },
            "steps": self.recovery_log
        }
        
        with open(filename, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"Recovery log saved to: {filename}")
    
    async def automated_recovery_assessment(self, environment: str) -> Optional[RecoveryPlan]:
        """Assess system status and recommend recovery plan"""
        print("🔍 Assessing system status for automated recovery...")
        
        # Check application health
        app_result = await self.execute_command([
            "kubectl", "get", "pods", 
            "-n", self.config["environments"][environment]["namespace"],
            "-l", "app=security-guard-ai",
            "-o", "json"
        ], 30)
        
        # Check database health
        db_result = await self.execute_command([
            "kubectl", "get", "pods",
            "-n", self.config["environments"][environment]["namespace"], 
            "-l", "app=postgres",
            "-o", "json"
        ], 30)
        
        app_healthy = False
        db_healthy = False
        
        if app_result["success"]:
            try:
                app_data = json.loads(app_result["stdout"])
                app_pods = app_data.get("items", [])
                running_app_pods = sum(1 for pod in app_pods if pod.get("status", {}).get("phase") == "Running")
                app_healthy = running_app_pods > 0
            except:
                pass
        
        if db_result["success"]:
            try:
                db_data = json.loads(db_result["stdout"])
                db_pods = db_data.get("items", [])
                running_db_pods = sum(1 for pod in db_pods if pod.get("status", {}).get("phase") == "Running")
                db_healthy = running_db_pods > 0
            except:
                pass
        
        print(f"Assessment results:")
        print(f"  Application healthy: {app_healthy}")
        print(f"  Database healthy: {db_healthy}")
        
        # Determine recovery plan
        if not app_healthy and not db_healthy:
            print("🚨 Complete system failure detected - recommending complete recovery")
            return self.get_complete_recovery_plan(environment)
        elif not db_healthy:
            print("🚨 Database failure detected - recommending database recovery")
            return self.get_database_recovery_plan(environment)
        elif not app_healthy:
            print("🚨 Application failure detected - recommending application recovery")
            return self.get_application_recovery_plan(environment)
        else:
            print("✅ System appears healthy - no recovery needed")
            return None

async def main():
    parser = argparse.ArgumentParser(description="SecurityGuard AI Disaster Recovery")
    parser.add_argument("--config", default="dr_config.json", help="Configuration file path")
    parser.add_argument("--environment", default="production", choices=["production", "staging"], help="Environment to recover")
    parser.add_argument("--plan", choices=["database", "application", "complete", "auto"], default="auto", help="Recovery plan to execute")
    parser.add_argument("--dry-run", action="store_true", help="Show recovery plan without executing")
    parser.add_argument("--log-file", help="Save recovery log to specific file")
    
    args = parser.parse_args()
    
    dr_manager = DisasterRecoveryManager(args.config)
    
    try:
        # Determine recovery plan
        if args.plan == "auto":
            plan = await dr_manager.automated_recovery_assessment(args.environment)
            if not plan:
                print("✅ No recovery needed - system is healthy")
                return
        elif args.plan == "database":
            plan = dr_manager.get_database_recovery_plan(args.environment)
        elif args.plan == "application":
            plan = dr_manager.get_application_recovery_plan(args.environment)
        elif args.plan == "complete":
            plan = dr_manager.get_complete_recovery_plan(args.environment)
        
        if args.dry_run:
            print(f"\n📋 Recovery Plan: {plan.name}")
            print(f"Description: {plan.description}")
            print(f"Estimated time: {plan.estimated_time_minutes} minutes")
            print(f"\nSteps:")
            for i, step in enumerate(plan.steps, 1):
                critical_marker = " (CRITICAL)" if step.critical else ""
                print(f"  {i}. {step.name}{critical_marker}")
                print(f"     {step.description}")
                print(f"     Command: {' '.join(step.command)}")
                print(f"     Timeout: {step.timeout_seconds}s")
                if step.rollback_command:
                    print(f"     Rollback: {' '.join(step.rollback_command)}")
                print()
            return
        
        # Execute recovery plan
        success = await dr_manager.execute_recovery_plan(plan)
        
        # Send notifications
        duration = (datetime.utcnow() - dr_manager.start_time).total_seconds()
        await dr_manager.send_recovery_notification(plan.name, success, duration)
        
        # Save log
        dr_manager.save_recovery_log(args.log_file)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Recovery interrupted by user")
        dr_manager.save_recovery_log()
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Recovery failed with exception: {e}")
        dr_manager.save_recovery_log()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())