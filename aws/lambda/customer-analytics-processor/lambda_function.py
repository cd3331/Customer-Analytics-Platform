
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
                    
                    lines = data.split('\n')
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
