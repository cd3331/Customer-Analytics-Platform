
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
