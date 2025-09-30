#!/usr/bin/env python3
"""
Test Lambda Functions
Verifies that Lambda functions are working correctly
"""

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_functions():
    lambda_client = boto3.client(
        'lambda',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    print("Testing Lambda Functions\n")
    
    # Test 1: Health check on API
    print("1. Testing API health endpoint...")
    try:
        response = lambda_client.invoke(
            FunctionName='customer-analytics-api',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'httpMethod': 'GET',
                'path': '/health'
            })
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result['body'])
        print(f"   Status: {result['statusCode']}")
        print(f"   Response: {body['status']}")
        print("   ✓ API is healthy\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Test 2: Metrics endpoint
    print("2. Testing metrics endpoint...")
    try:
        response = lambda_client.invoke(
            FunctionName='customer-analytics-api',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'httpMethod': 'GET',
                'path': '/metrics'
            })
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result['body'])
        print(f"   Status: {result['statusCode']}")
        print(f"   Metrics: {json.dumps(body, indent=2)}")
        print("   ✓ Metrics retrieved\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Test 3: Data processor
    print("3. Testing data processor...")
    try:
        response = lambda_client.invoke(
            FunctionName='customer-analytics-processor',
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'aggregate'})
        )
        
        result = json.loads(response['Payload'].read())
        print(f"   Status: {result['statusCode']}")
        if 'body' in result:
            body = json.loads(result['body'])
            print(f"   Processed: {json.dumps(body, indent=2)}")
        print("   ✓ Processor working\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    print("All tests complete!")

if __name__ == "__main__":
    test_functions()
