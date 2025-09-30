#!/usr/bin/env python3
"""
AWS Lambda Setup Script
Deploys Lambda functions for data processing and API endpoints
Creates necessary IAM roles and permissions
"""

import os
import sys
import boto3
import json
import zipfile
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import time

load_dotenv()

class LambdaManager:
    def __init__(self):
        try:
            self.lambda_client = boto3.client(
                'lambda',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.iam_client = boto3.client(
                'iam',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            self.account_id = os.getenv('AWS_ACCOUNT_ID')
            self.region = os.getenv('AWS_REGION', 'us-east-1')
            self.s3_bucket = os.getenv('S3_BUCKET_NAME')
            self.dynamodb_table = os.getenv('DYNAMODB_TABLE', 'customer-behavior')
            
            print("AWS Lambda client initialized successfully")
            
        except Exception as e:
            print(f"ERROR initializing Lambda client: {e}")
            sys.exit(1)

    def create_lambda_role(self):
        """Create IAM role for Lambda execution"""
        
        role_name = 'customer-analytics-lambda-role'
        
        # Check if role exists
        try:
            self.iam_client.get_role(RoleName=role_name)
            print(f"IAM role {role_name} already exists")
            return f"arn:aws:iam::{self.account_id}:role/{role_name}"
        except:
            pass
        
        print(f"Creating IAM role: {role_name}")
        
        # Trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        try:
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for Customer Analytics Lambda functions',
                Tags=[
                    {'Key': 'Project', 'Value': 'CustomerAnalytics'},
                    {'Key': 'Environment', 'Value': 'Development'}
                ]
            )
            
            role_arn = response['Role']['Arn']
            print(f"Created role: {role_arn}")
            
            # Attach policies (broad for demo; tighten in prod)
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
            ]
            for policy in policies:
                self.iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy)
            print("Attached necessary policies")
            
            # Wait for role to propagate
            time.sleep(10)
            return role_arn
            
        except ClientError as e:
            print(f"ERROR creating role: {e}")
            return None

    def create_lambda_package(self, function_name, code):
        """Create deployment package for Lambda"""
        
        package_dir = Path(f"aws/lambda/{function_name}")
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Write function code
        function_file = package_dir / "lambda_function.py"
        with open(function_file, 'w') as f:
            f.write(code)
        
        # Create zip file
        zip_path = package_dir / f"{function_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(function_file, 'lambda_function.py')
        
        print(f"Created deployment package: {zip_path}")
        return str(zip_path)

    def deploy_data_processor(self, role_arn):
        """Deploy Lambda function for data processing"""
        
        function_name = 'customer-analytics-processor'
        
        # Lambda function code
        code = '''
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """Process incoming customer data and store metrics"""
    
    try:
        # Get environment variables
        bucket_name = os.environ.get('S3_BUCKET')
        table_name = os.environ.get('DYNAMODB_TABLE')
        
        # Process S3 event (if triggered by S3)
        if 'Records' in event:
            for record in event['Records']:
                if 's3' in record:
                    bucket = record['s3']['bucket']['name']
                    key = record['s3']['object']['key']
                    
                    response = s3.get_object(Bucket=bucket, Key=key)
                    data = response['Body'].read().decode('utf-8')
                    
                    lines = data.split('\\n')
                    record_count = len(lines) - 1  # Exclude header
                    
                    print(f"Processed {key}: {record_count} records")
                    
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'message': f'Processed {record_count} records from {key}'
                        })
                    }
        
        # Process direct invocation
        if 'action' in event:
            if event['action'] == 'aggregate':
                table = dynamodb.Table(table_name)
                response = table.scan(Limit=100)
                items = response['Items']
                
                total_sessions = len(items)
                total_conversions = sum(1 for item in items if item.get('converted'))
                
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'total_sessions': total_sessions,
                    'total_conversions': total_conversions,
                    'conversion_rate': (total_conversions / total_sessions * 100) if total_sessions > 0 else 0
                }
                
                s3.put_object(
                    Bucket=bucket_name,
                    Key=f'metrics/{datetime.now().strftime("%Y%m%d_%H%M%S")}_metrics.json',
                    Body=json.dumps(metrics, default=str),
                    ContentType='application/json'
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(metrics, default=str)
                }
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Data processor ready'})
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
        
        # Create deployment package
        zip_path = self.create_lambda_package(function_name, code)
        
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        try:
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                print(f"Updating existing function: {function_name}")
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                print(f"Creating new function: {function_name}")
                self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.11',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_content},
                    Description='Process customer analytics data',
                    Timeout=60,
                    MemorySize=256,
                    Environment={
                        'Variables': {
                            'S3_BUCKET': self.s3_bucket,
                            'DYNAMODB_TABLE': self.dynamodb_table
                        }
                    },
                    Tags={
                        'Project': 'CustomerAnalytics',
                        'Environment': 'Development'
                    }
                )
            print(f"SUCCESS: Deployed {function_name}")
            return True
        except ClientError as e:
            print(f"ERROR deploying function: {e}")
            return False

    def deploy_api_handler(self, role_arn):
        """Deploy Lambda function for API endpoints"""
        
        function_name = 'customer-analytics-api'
        
        # Lambda function code for API
        code = '''
import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    """Handle API requests for customer analytics"""
    
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
        
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
            }
        
        elif path == '/customer' and http_method == 'GET':
            params = event.get('queryStringParameters', {}) or {}
            customer_id = params.get('customer_id')
            if not customer_id:
                return {'statusCode': 400, 'body': json.dumps({'error': 'customer_id parameter required'})}
            
            response = table.query(
                KeyConditionExpression='customer_id = :cid',
                ExpressionAttributeValues={':cid': customer_id}
            )
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'customer_id': customer_id,
                    'sessions': response['Items'],
                    'total_sessions': response['Count']
                }, cls=DecimalEncoder)
            }
        
        elif path == '/metrics' and http_method == 'GET':
            response = table.scan(Limit=100)
            items = response['Items']
            total_sessions = len(items)
            conversions = sum(1 for item in items if item.get('converted'))
            total_revenue = sum(float(item.get('cart_value', 0)) for item in items)
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'total_sessions': total_sessions,
                'conversions': conversions,
                'conversion_rate': round((conversions / total_sessions * 100) if total_sessions > 0 else 0, 2),
                'total_revenue': round(total_revenue, 2),
                'avg_cart_value': round((total_revenue / conversions) if conversions > 0 else 0, 2)
            }
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(metrics)}
        
        elif path == '/trigger-processing' and http_method == 'POST':
            lambda_client = boto3.client('lambda')
            response = lambda_client.invoke(
                FunctionName='customer-analytics-processor',
                InvocationType='Event',
                Payload=json.dumps({'action': 'aggregate'})
            )
            return {'statusCode': 202, 'body': json.dumps({'message': 'Processing triggered', 'requestId': response['ResponseMetadata']['RequestId']})}
        
        else:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Endpoint not found'})}
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
'''
        
        # Create deployment package
        zip_path = self.create_lambda_package(function_name, code)
        
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

        try:
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                print(f"Updating existing function: {function_name}")
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                print(f"Creating new function: {function_name}")
                self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.11',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_content},
                    Description='API handler for customer analytics',
                    Timeout=30,
                    MemorySize=256,
                    Environment={
                        'Variables': {
                            'S3_BUCKET': self.s3_bucket,
                            'DYNAMODB_TABLE': self.dynamodb_table
                        }
                    },
                    Tags={
                        'Project': 'CustomerAnalytics',
                        'Environment': 'Development'
                    }
                )
            print(f"SUCCESS: Deployed {function_name}")
            return True
        except ClientError as e:
            print(f"ERROR deploying function: {e}")
            return False

    def test_functions(self):
        """Test deployed Lambda functions"""
        
        print("\nTesting Lambda functions...")
        
        # Test data processor
        try:
            response = self.lambda_client.invoke(
                FunctionName='customer-analytics-processor',
                InvocationType='RequestResponse',
                Payload=json.dumps({'action': 'aggregate'})
            )
            result = json.loads(response['Payload'].read())
            print(f"Data Processor Test: {result.get('statusCode')} - Success")
        except Exception as e:
            print(f"Data Processor Test Failed: {e}")
        
        # Test API handler
        try:
            response = self.lambda_client.invoke(
                FunctionName='customer-analytics-api',
                InvocationType='RequestResponse',
                Payload=json.dumps({'httpMethod': 'GET','path': '/health'})
            )
            result = json.loads(response['Payload'].read())
            print(f"API Handler Test: {result.get('statusCode')} - Success")
        except Exception as e:
            print(f"API Handler Test Failed: {e}")
    
    def save_config(self):
        """Save Lambda configuration"""
        
        config = {
            'functions': {
                'processor': 'customer-analytics-processor',
                'api': 'customer-analytics-api'
            },
            'region': self.region,
            'created_at': datetime.now().isoformat()
        }
        
        config_path = Path('config/aws/lambda_config.json')
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {config_path}")
    
    def get_function_urls(self):
        """Get function ARNs and info"""
        
        print("\nFunction Information:")
        functions = ['customer-analytics-processor', 'customer-analytics-api']
        for function_name in functions:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                print(f"\n{function_name}:")
                print(f"  ARN: {response['Configuration']['FunctionArn']}")
                print(f"  Runtime: {response['Configuration']['Runtime']}")
                print(f"  Memory: {response['Configuration']['MemorySize']} MB")
                print(f"  Timeout: {response['Configuration']['Timeout']} seconds")
            except:
                pass

def main():
    print("="*50)
    print("AWS Lambda Setup for Customer Analytics Platform")
    print("="*50)
    
    manager = LambdaManager()
    
    # Create IAM role
    role_arn = manager.create_lambda_role()
    if not role_arn:
        print("Failed to create IAM role")
        sys.exit(1)
    
    # Deploy functions
    manager.deploy_data_processor(role_arn)
    manager.deploy_api_handler(role_arn)
    
    # Test functions
    manager.test_functions()
    
    # Get function info
    manager.get_function_urls()
    
    # Save configuration
    manager.save_config()
    
    print("\n" + "="*50)
    print("Lambda Setup Complete!")
    print("\nDeployed Functions:")
    print("1. customer-analytics-processor - Data processing")
    print("2. customer-analytics-api - API endpoints")
    print("\nNext steps:")
    print("1. Set up API Gateway: python scripts/aws_api_gateway_setup.py")
    print("2. Test the complete pipeline: python scripts/test_pipeline.py")
    print("="*50)

if __name__ == "__main__":
    main()
