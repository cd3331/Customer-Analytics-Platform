#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime

def check_python_version():
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ is required")
        sys.exit(1)
    print(f"OK: Python {sys.version.split()[0]} detected")

def check_aws_cli():
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        print(f"OK: AWS CLI detected")
        return True
    except FileNotFoundError:
        print("WARNING: AWS CLI not found")
        return False

def check_environment_file():
    if not Path('.env').exists():
        print("WARNING: .env file not found. Creating from .env.example...")
        if Path('.env.example').exists():
            subprocess.run(['cp', '.env.example', '.env'])
        print("Please edit .env file with your credentials")
        return False
    print("OK: .env file found")
    return True

def create_data_folders():
    folders = [
        'data/raw/sales',
        'data/raw/marketing',
        'data/raw/behavior',
        'data/raw/support',
        'data/raw/events',
        'data/raw/products',
        'data/processed',
        'data/sample',
        'outputs/reports',
        'outputs/models',
        'outputs/logs'
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    print("OK: Data folders created")

def create_config_files():
    aws_config = {
        "region": "us-east-1",
        "services": {
            "s3": {
                "bucket_name": f"customer-analytics-demo-{datetime.now().strftime('%Y%m%d')}",
                "free_tier_limit_gb": 5
            },
            "rds": {
                "instance_class": "db.t3.micro",
                "free_tier_hours": 750
            },
            "lambda": {
                "free_tier_requests": 1000000,
                "free_tier_gb_seconds": 400000
            },
            "dynamodb": {
                "free_tier_storage_gb": 25
            }
        },
        "cost_alerts": {
            "daily_limit": 0.50,
            "monthly_limit": 5.00
        }
    }
    
    Path('config/aws').mkdir(parents=True, exist_ok=True)
    
    with open('config/aws/config.yaml', 'w') as f:
        import yaml
        yaml.dump(aws_config, f, default_flow_style=False)
    
    print("OK: Configuration files created")

def main():
    print("\nCustomer Analytics Platform - Initial Setup\n")
    print("=" * 50)
    
    check_python_version()
    aws_installed = check_aws_cli()
    env_exists = check_environment_file()
    create_data_folders()
    create_config_files()
    
    print("\n" + "=" * 50)
    
    if not env_exists:
        print("\nACTION REQUIRED:")
        print("1. Edit .env file with your AWS credentials")
        print("2. Run 'python setup.py' again to validate")
    else:
        print("\nSetup complete! Next steps:")
        print("1. Run: python scripts/data-generation/generate_sample_data.py")
        print("2. Configure AWS services")
    
    print("\nDocumentation: docs/README.md")

if __name__ == "__main__":
    main()
