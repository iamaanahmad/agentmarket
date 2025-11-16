#!/usr/bin/env python3
"""
Backup and disaster recovery scripts for SecurityGuard AI
Handles database backups, configuration backups, and restore procedures
"""
import os
import sys
import subprocess
import boto3
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

class BackupManager:
    def __init__(self, config_file: str = "backup_config.json"):
        self.config = self.load_config(config_file)
        self.s3_client = None
        
        if self.config.get("aws_enabled", False):
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.get("aws_access_key_id"),
                aws_secret_access_key=self.config.get("aws_secret_access_key"),
                region_name=self.config.get("aws_region", "us-east-1")
            )
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load backup configuration"""
        default_config = {
            "database_url": os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/securityguard"),
            "backup_directory": "/backups",
            "retention_days": 30,
            "aws_enabled": False,
            "aws_bucket": "securityguard-backups",
            "aws_region": "us-east-1",
            "compress_backups": True,
            "backup_schedule": {
                "database": "daily",
                "logs": "weekly",
                "config": "daily"
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
    
    def create_backup_directory(self):
        """Ensure backup directory exists"""
        backup_dir = Path(self.config["backup_directory"])
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def backup_database(self) -> str:
        """Create database backup using pg_dump"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.create_backup_directory()
        backup_file = backup_dir / f"database_backup_{timestamp}.sql"
        
        try:
            # Extract database connection details
            db_url = self.config["database_url"]
            
            # Use pg_dump to create backup
            cmd = [
                "pg_dump",
                db_url,
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
                "--create",
                "--file", str(backup_file)
            ]
            
            print(f"Creating database backup: {backup_file}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Compress backup if enabled
            if self.config["compress_backups"]:
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                os.remove(backup_file)
                backup_file = compressed_file
            
            print(f"Database backup completed: {backup_file}")
            
            # Upload to S3 if enabled
            if self.s3_client:
                self.upload_to_s3(backup_file, f"database/{os.path.basename(backup_file)}")
            
            return str(backup_file)
            
        except Exception as e:
            print(f"Database backup failed: {e}")
            raise
    
    def backup_application_logs(self) -> str:
        """Backup application logs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.create_backup_directory()
        logs_backup = backup_dir / f"logs_backup_{timestamp}.tar.gz"
        
        try:
            # Define log directories to backup
            log_dirs = [
                "/app/logs",
                "/var/log/nginx",
                "./security-ai/logs"
            ]
            
            # Create tar archive of log files
            cmd = ["tar", "-czf", str(logs_backup)]
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    cmd.append(log_dir)
            
            if len(cmd) > 3:  # Only run if we have directories to backup
                print(f"Creating logs backup: {logs_backup}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"Logs backup failed: {result.stderr}")
                
                print(f"Logs backup completed: {logs_backup}")
                
                # Upload to S3 if enabled
                if self.s3_client:
                    self.upload_to_s3(logs_backup, f"logs/{os.path.basename(logs_backup)}")
                
                return str(logs_backup)
            else:
                print("No log directories found to backup")
                return ""
                
        except Exception as e:
            print(f"Logs backup failed: {e}")
            raise
    
    def backup_configuration(self) -> str:
        """Backup configuration files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.create_backup_directory()
        config_backup = backup_dir / f"config_backup_{timestamp}.tar.gz"
        
        try:
            # Define configuration files and directories to backup
            config_items = [
                "docker-compose.yml",
                "nginx/nginx.conf",
                "monitoring/",
                ".env",
                "backup_config.json"
            ]
            
            # Create tar archive of configuration files
            cmd = ["tar", "-czf", str(config_backup)]
            
            for item in config_items:
                if os.path.exists(item):
                    cmd.append(item)
            
            if len(cmd) > 3:  # Only run if we have items to backup
                print(f"Creating configuration backup: {config_backup}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"Configuration backup failed: {result.stderr}")
                
                print(f"Configuration backup completed: {config_backup}")
                
                # Upload to S3 if enabled
                if self.s3_client:
                    self.upload_to_s3(config_backup, f"config/{os.path.basename(config_backup)}")
                
                return str(config_backup)
            else:
                print("No configuration files found to backup")
                return ""
                
        except Exception as e:
            print(f"Configuration backup failed: {e}")
            raise
    
    def upload_to_s3(self, local_file: str, s3_key: str):
        """Upload backup file to S3"""
        try:
            bucket = self.config["aws_bucket"]
            print(f"Uploading {local_file} to s3://{bucket}/{s3_key}")
            
            self.s3_client.upload_file(local_file, bucket, s3_key)
            print(f"Successfully uploaded to S3: {s3_key}")
            
        except Exception as e:
            print(f"S3 upload failed: {e}")
            raise
    
    def restore_database(self, backup_file: str):
        """Restore database from backup"""
        try:
            # Check if backup file is compressed
            if backup_file.endswith('.gz'):
                # Decompress first
                decompressed_file = backup_file[:-3]
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_file = decompressed_file
            
            # Restore using psql
            db_url = self.config["database_url"]
            
            cmd = [
                "psql",
                db_url,
                "--file", backup_file,
                "--verbose"
            ]
            
            print(f"Restoring database from: {backup_file}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Database restore failed: {result.stderr}")
            
            print("Database restore completed successfully")
            
        except Exception as e:
            print(f"Database restore failed: {e}")
            raise
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            backup_dir = Path(self.config["backup_directory"])
            retention_days = self.config["retention_days"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            if not backup_dir.exists():
                return
            
            deleted_count = 0
            for backup_file in backup_dir.glob("*_backup_*"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    print(f"Removing old backup: {backup_file}")
                    backup_file.unlink()
                    deleted_count += 1
            
            print(f"Cleaned up {deleted_count} old backup files")
            
        except Exception as e:
            print(f"Backup cleanup failed: {e}")
    
    def create_full_backup(self) -> Dict[str, str]:
        """Create complete system backup"""
        print("Starting full system backup...")
        
        backups = {}
        
        try:
            # Database backup
            backups["database"] = self.backup_database()
            
            # Logs backup
            logs_backup = self.backup_application_logs()
            if logs_backup:
                backups["logs"] = logs_backup
            
            # Configuration backup
            config_backup = self.backup_configuration()
            if config_backup:
                backups["config"] = config_backup
            
            # Cleanup old backups
            self.cleanup_old_backups()
            
            print("Full system backup completed successfully")
            return backups
            
        except Exception as e:
            print(f"Full backup failed: {e}")
            raise
    
    def list_backups(self) -> Dict[str, list]:
        """List available backups"""
        backup_dir = Path(self.config["backup_directory"])
        
        if not backup_dir.exists():
            return {"local": [], "s3": []}
        
        # Local backups
        local_backups = []
        for backup_file in backup_dir.glob("*_backup_*"):
            stat = backup_file.stat()
            local_backups.append({
                "file": str(backup_file),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # S3 backups (if enabled)
        s3_backups = []
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.config["aws_bucket"]
                )
                
                for obj in response.get("Contents", []):
                    s3_backups.append({
                        "key": obj["Key"],
                        "size_mb": round(obj["Size"] / (1024 * 1024), 2),
                        "created": obj["LastModified"].isoformat()
                    })
            except Exception as e:
                print(f"Could not list S3 backups: {e}")
        
        return {
            "local": sorted(local_backups, key=lambda x: x["created"], reverse=True),
            "s3": sorted(s3_backups, key=lambda x: x["created"], reverse=True)
        }

def main():
    parser = argparse.ArgumentParser(description="SecurityGuard AI Backup and Recovery")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup"],
                       help="Action to perform")
    parser.add_argument("--type", choices=["database", "logs", "config", "full"],
                       default="full", help="Type of backup")
    parser.add_argument("--file", help="Backup file for restore operation")
    parser.add_argument("--config", default="backup_config.json",
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    backup_manager = BackupManager(args.config)
    
    try:
        if args.action == "backup":
            if args.type == "database":
                result = backup_manager.backup_database()
                print(f"Database backup created: {result}")
            elif args.type == "logs":
                result = backup_manager.backup_application_logs()
                print(f"Logs backup created: {result}")
            elif args.type == "config":
                result = backup_manager.backup_configuration()
                print(f"Configuration backup created: {result}")
            elif args.type == "full":
                results = backup_manager.create_full_backup()
                print("Full backup completed:")
                for backup_type, file_path in results.items():
                    print(f"  {backup_type}: {file_path}")
        
        elif args.action == "restore":
            if not args.file:
                print("Error: --file argument required for restore operation")
                sys.exit(1)
            
            if args.type == "database":
                backup_manager.restore_database(args.file)
                print("Database restore completed")
            else:
                print("Error: Only database restore is currently supported")
                sys.exit(1)
        
        elif args.action == "list":
            backups = backup_manager.list_backups()
            print("\nAvailable Backups:")
            print("\nLocal Backups:")
            for backup in backups["local"]:
                print(f"  {backup['file']} ({backup['size_mb']} MB) - {backup['created']}")
            
            if backups["s3"]:
                print("\nS3 Backups:")
                for backup in backups["s3"]:
                    print(f"  {backup['key']} ({backup['size_mb']} MB) - {backup['created']}")
        
        elif args.action == "cleanup":
            backup_manager.cleanup_old_backups()
            print("Backup cleanup completed")
    
    except Exception as e:
        print(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()