#!/usr/bin/env python3
"""
Alteryx Designer Cloud Setup and Integration
Connects to AWS data sources and builds analytics workflow
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
def create_alteryx_config():
    """Create configuration for Alteryx Designer Cloud"""
    
    config = {
        "alteryx_setup": {
            "trial_url": "https://www.alteryx.com/designer-cloud-trial",
            "duration": "30 days",
            "steps": [
                "1. Sign up at the URL above with business email",
                "2. Verify email immediately", 
                "3. Log in to https://designercloud.alteryx.com",
                "4. Configure AWS connections (see connections below)"
            ]
        },
        "aws_connections": {
            "s3_connection": {
                "name": "CustomerAnalyticsS3",
                "type": "Amazon S3",
                "configuration": {
                    "accessKeyId": os.getenv('AWS_ACCESS_KEY_ID'),
                    "secretAccessKey": "***HIDDEN***",
                    "region": os.getenv('AWS_REGION'),
                    "bucket": os.getenv('S3_BUCKET_NAME')
                }
            },
            "rds_connection": {
                "name": "CustomerAnalyticsRDS",
                "type": "MySQL",
                "configuration": {
                    "host": os.getenv('RDS_HOST'),
                    "port": 3306,
                    "database": os.getenv('RDS_DATABASE'),
                    "username": os.getenv('RDS_USERNAME'),
                    "password": "***HIDDEN***"
                }
            },
            "athena_connection": {
                "name": "CustomerAnalyticsAthena",
                "type": "Amazon Athena",
                "configuration": {
                    "workgroup": "primary",
                    "database": "customer_analytics_db",
                    "s3OutputLocation": f"s3://{os.getenv('S3_BUCKET_NAME')}/athena-results/"
                }
            }
        },
        "workflow_template": {
            "name": "Customer_360_Analytics",
            "description": "End-to-end customer analytics workflow",
            "tools": [
                {
                    "step": 1,
                    "tool": "Input Data",
                    "source": "S3",
                    "path": "data/sales/sales_data.csv"
                },
                {
                    "step": 2,
                    "tool": "Input Data", 
                    "source": "RDS MySQL",
                    "query": "SELECT * FROM campaign_responses"
                },
                {
                    "step": 3,
                    "tool": "Join",
                    "type": "Inner Join",
                    "key": "customer_id"
                },
                {
                    "step": 4,
                    "tool": "Formula",
                    "calculations": [
                        "CLV = [total_purchases] * [avg_order_value]",
                        "Churn_Risk = IF [days_since_purchase] > 60 THEN 'High' ELSE 'Low' ENDIF"
                    ]
                },
                {
                    "step": 5,
                    "tool": "Predictive",
                    "model": "Classification",
                    "target": "churn_flag"
                },
                {
                    "step": 6,
                    "tool": "Output Data",
                    "destination": "S3",
                    "path": "output/customer_360.csv"
                }
            ]
        }
    }
    
    # Save configuration
    config_path = Path('config/alteryx/alteryx_config.json')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Alteryx configuration created at:", config_path)
    print("\nNext steps:")
    print("1. Sign up for Alteryx Designer Cloud trial")
    print("2. Import the configuration")
    print("3. Build the workflow using the template")
    
    return config

def create_workflow_instructions():
    """Create step-by-step workflow building instructions"""
    
    instructions = """# Alteryx Designer Cloud Workflow Setup

## Prerequisites
- Alteryx Designer Cloud trial account
- AWS credentials configured
- Data already in S3/RDS/DynamoDB

## Step-by-Step Workflow Creation

### 1. Log into Alteryx Designer Cloud
- URL: https://designercloud.alteryx.com
- Use your trial account credentials

### 2. Create New Workflow
- Click "Create New"
- Select "Workflow"
- Name: "Customer_360_Analytics"

### 3. Configure Data Connections

#### S3 Connection:
1. Click "Connections" → "Add Connection"
2. Select "Amazon S3"
3. Enter AWS credentials
4. Test connection

#### RDS Connection:
1. Add Connection → MySQL
2. Enter RDS endpoint from your .env
3. Database: marketing_db
4. Test connection

### 4. Build the Workflow

#### Step 1: Input Sales Data
- Drag "Input Data" tool
- Select S3 connection
- Browse to: data/sales/sales_data.csv
- Preview data

#### Step 2: Input Marketing Data
- Add second "Input Data" tool
- Select RDS connection
- Custom SQL Query

#### Step 3: Join Data
- Add "Join" tool
- Connect both inputs
- Join on: customer_id
- Type: Left Join

#### Step 4: Create Calculated Fields
- Add "Formula" tool
- Create new calculated fields for analysis

#### Step 5: Output Results
- Add "Output Data" tool
- Destination: S3
- Path: output/customer_analytics_results.csv

### 5. Run Workflow
- Click "Run Now"
- Monitor progress
- Check outputs in S3

## Expected Outputs
- customer_analytics_results.csv
- model_performance_metrics.json
- customer_segments.csv
"""
    
    # Save instructions
    instructions_path = Path('docs/alteryx_workflow_instructions.md')
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(instructions_path, 'w') as f:
        f.write(instructions)
    
    print(f"Instructions saved to: {instructions_path}")

if __name__ == "__main__":
    config = create_alteryx_config()
    create_workflow_instructions()
