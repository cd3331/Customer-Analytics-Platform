# Lambda Function Development Guide

## Overview

This guide covers developing, testing, and deploying AWS Lambda functions for the Customer Analytics Platform.

## Project Structure

```
aws/lambda/
├── customer-analytics-api/
│   ├── lambda_function.py    # Main handler
│   ├── requirements.txt      # Dependencies
│   └── README.md            # Function documentation
└── customer-analytics-processor/
    ├── lambda_function.py
    ├── requirements.txt
    └── README.md
```

## Lambda Function Overview

### customer-analytics-api

**Purpose:** REST API for customer analytics data

**Trigger:** API Gateway HTTP requests

**Runtime:** Python 3.11

**Endpoints:**
- `GET /health` - Health check
- `GET /customer` - Get customer details
- `GET /metrics` - Get aggregated metrics
- `POST /trigger-processing` - Trigger data processing

**Environment Variables:**
- `DYNAMODB_TABLE` - DynamoDB table name
- `S3_BUCKET` - S3 bucket for data
- `REGION` - AWS region

### customer-analytics-processor

**Purpose:** Background data aggregation and processing

**Trigger:** S3 upload events, scheduled events (EventBridge)

**Runtime:** Python 3.11

**Tasks:**
- Aggregate customer behavioral data
- Calculate derived metrics
- Update summary tables
- Generate reports

## Development Setup

### Local Development Environment

1. **Install dependencies:**
   ```bash
   cd aws/lambda/customer-analytics-api
   pip install -r requirements.txt
   ```

2. **Set up local environment variables:**
   ```bash
   export DYNAMODB_TABLE=customer-behavior-events
   export S3_BUCKET=customer-analytics-dev
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **Run locally:**
   ```python
   # test_local.py
   from lambda_function import lambda_handler

   event = {
       'httpMethod': 'GET',
       'path': '/health',
       'queryStringParameters': None
   }

   result = lambda_handler(event, None)
   print(result)
   ```

### Testing with SAM CLI

AWS SAM (Serverless Application Model) provides local testing:

1. **Install SAM CLI:**
   ```bash
   pip install aws-sam-cli
   ```

2. **Create SAM template:**
   ```yaml
   # template.yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Transform: AWS::Serverless-2016-10-31

   Resources:
     CustomerAnalyticsAPI:
       Type: AWS::Serverless::Function
       Properties:
         Handler: lambda_function.lambda_handler
         Runtime: python3.11
         CodeUri: aws/lambda/customer-analytics-api/
         Environment:
           Variables:
             DYNAMODB_TABLE: customer-behavior-events
             S3_BUCKET: customer-analytics-dev
         Events:
           ApiEvent:
             Type: Api
             Properties:
               Path: /{proxy+}
               Method: ANY
   ```

3. **Test locally:**
   ```bash
   # Start local API
   sam local start-api

   # Invoke function directly
   sam local invoke CustomerAnalyticsAPI -e events/test-event.json
   ```

### Testing with Docker

Use the official Lambda container images:

```dockerfile
# Dockerfile
FROM public.ecr.aws/lambda/python:3.11

COPY lambda_function.py requirements.txt ./
RUN pip install -r requirements.txt

CMD ["lambda_function.lambda_handler"]
```

```bash
# Build and run
docker build -t customer-analytics-api .
docker run -p 9000:8080 \
  -e DYNAMODB_TABLE=customer-behavior-events \
  customer-analytics-api

# Test
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"httpMethod": "GET", "path": "/health"}'
```

## Writing Lambda Functions

### Handler Function

The entry point for Lambda execution:

```python
def lambda_handler(event, context):
    """
    Main Lambda handler

    Args:
        event (dict): Event data from trigger
        context (LambdaContext): Runtime information

    Returns:
        dict: Response with statusCode and body
    """
    try:
        # Your code here
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Success'})
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Best Practices

#### 1. Initialize Outside Handler

Resources initialized outside the handler are reused across invocations:

```python
import boto3

# Initialize outside handler (reused across invocations)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def lambda_handler(event, context):
    # Use pre-initialized resources
    response = table.get_item(Key={'id': '123'})
    return response
```

#### 2. Use Environment Variables

```python
import os

# Access environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE')
BUCKET_NAME = os.environ.get('S3_BUCKET')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Validate required variables
if not TABLE_NAME:
    raise ValueError("DYNAMODB_TABLE environment variable not set")
```

#### 3. Implement Proper Error Handling

```python
import traceback

def lambda_handler(event, context):
    try:
        # Main logic
        result = process_data(event)
        return success_response(result)

    except ClientError as e:
        # AWS service errors
        print(f"AWS Error: {e.response['Error']['Code']}")
        return error_response(500, "Service error")

    except ValueError as e:
        # Validation errors
        print(f"Validation Error: {str(e)}")
        return error_response(400, "Invalid input")

    except Exception as e:
        # Unexpected errors
        print(f"Unexpected Error: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, "Internal error")

def success_response(data):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data)
    }

def error_response(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }
```

#### 4. Implement Logging

```python
import logging

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Processing request: {event.get('path')}")

    # Log important events
    logger.info(f"Customer ID: {customer_id}")
    logger.warning(f"Rate limit approaching for {user_id}")
    logger.error(f"Failed to process {item_id}: {error}")

    return response
```

#### 5. Handle Timeouts

```python
import time

def lambda_handler(event, context):
    # Check remaining time
    remaining_time = context.get_remaining_time_in_millis()

    # Stop processing if running low on time
    if remaining_time < 5000:  # Less than 5 seconds
        logger.warning("Running low on time, returning partial results")
        return partial_response()

    # Continue processing
    return full_response()
```

## Testing

### Unit Tests

```python
# tests/test_lambda_function.py
import pytest
from lambda_function import lambda_handler

def test_health_check():
    event = {
        'httpMethod': 'GET',
        'path': '/health',
        'queryStringParameters': None
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    assert 'healthy' in response['body']

def test_missing_customer_id():
    event = {
        'httpMethod': 'GET',
        'path': '/customer',
        'queryStringParameters': None
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 400
```

### Integration Tests with Moto

Use `moto` to mock AWS services:

```python
import boto3
from moto import mock_dynamodb
import pytest
from lambda_function import lambda_handler

@mock_dynamodb
def test_get_customer():
    # Create mock DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='customer-behavior-events',
        KeySchema=[
            {'AttributeName': 'customer_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'customer_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Add test data
    table.put_item(Item={
        'customer_id': 'CUST0001',
        'timestamp': 1234567890,
        'event_type': 'purchase'
    })

    # Test Lambda function
    event = {
        'httpMethod': 'GET',
        'path': '/customer',
        'queryStringParameters': {'customer_id': 'CUST0001'}
    }

    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
```

## Deployment

### Manual Deployment

```bash
# Package Lambda function
cd aws/lambda/customer-analytics-api
zip -r function.zip lambda_function.py

# Install dependencies
pip install -r requirements.txt -t .
zip -r function.zip .

# Deploy
aws lambda update-function-code \
  --function-name customer-analytics-api \
  --zip-file fileb://function.zip
```

### Automated Deployment Script

```python
# scripts/aws_lambda_setup.py
import boto3
import zipfile
import os

def deploy_lambda(function_name, handler, runtime, role_arn):
    lambda_client = boto3.client('lambda')

    # Create deployment package
    zip_path = create_deployment_package(function_name)

    try:
        # Update existing function
        with open(zip_path, 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=f.read()
            )
        print(f"Updated {function_name}")

    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        with open(zip_path, 'rb') as f:
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime=runtime,
                Role=role_arn,
                Handler=handler,
                Code={'ZipFile': f.read()},
                Timeout=60,
                MemorySize=256
            )
        print(f"Created {function_name}")
```

## Monitoring & Debugging

### CloudWatch Logs

```bash
# Tail logs
aws logs tail /aws/lambda/customer-analytics-api --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/customer-analytics-api \
  --filter-pattern "ERROR"

# Get specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/customer-analytics-api \
  --start-time 1610000000000 \
  --end-time 1610003600000
```

### CloudWatch Metrics

Key metrics to monitor:
- **Invocations:** Total number of executions
- **Errors:** Failed executions
- **Duration:** Execution time
- **Throttles:** Rate-limited requests
- **ConcurrentExecutions:** Concurrent invocations

### X-Ray Tracing

Enable for distributed tracing:

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch AWS SDK
patch_all()

def lambda_handler(event, context):
    # Create subsegment
    with xray_recorder.capture('process_customer'):
        result = process_customer(customer_id)

    return result
```

## Performance Optimization

### Memory Tuning

Lambda CPU scales with memory allocation. Test different configurations:

```bash
# Test with 256 MB
aws lambda update-function-configuration \
  --function-name customer-analytics-api \
  --memory-size 256

# Test with 512 MB
aws lambda update-function-configuration \
  --function-name customer-analytics-api \
  --memory-size 512
```

### Provisioned Concurrency

Pre-warm instances for consistent performance:

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name customer-analytics-api \
  --provisioned-concurrent-executions 5 \
  --qualifier $LATEST
```

### Lambda Layers

Extract common dependencies to layers:

```bash
# Create layer
mkdir python
pip install requests -t python/
zip -r layer.zip python

aws lambda publish-layer-version \
  --layer-name common-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

## Security Best Practices

1. **Least Privilege IAM Roles:** Grant only required permissions
2. **Environment Variable Encryption:** Use KMS for sensitive data
3. **VPC Configuration:** Isolate functions in private subnets
4. **Input Validation:** Sanitize all user inputs
5. **Dependency Scanning:** Regularly update dependencies

## Additional Resources

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Lambda Powertools Python](https://awslabs.github.io/aws-lambda-powertools-python/)

---

**Last Updated:** 2024-01-15
**Version:** 1.0
