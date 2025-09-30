#!/usr/bin/env python3
"""
AWS DynamoDB Setup Script
Creates DynamoDB tables for customer behavior tracking
Inserts sample data within free tier limits
"""

import os
import sys
import boto3
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

class DynamoDBManager:
    def __init__(self):
        try:
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.client = boto3.client(
                'dynamodb',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            self.table_name = 'customer-behavior'
            self.table = None
            
            print("AWS DynamoDB client initialized successfully")
            
        except Exception as e:
            print(f"ERROR initializing DynamoDB client: {e}")
            sys.exit(1)

    def create_behavior_table(self):
        """Create customer behavior tracking table"""
        
        print(f"\nCreating DynamoDB table: {self.table_name}")
        
        try:
            # Check if table exists
            existing_tables = self.client.list_tables()['TableNames']
            if self.table_name in existing_tables:
                print(f"Table {self.table_name} already exists")
                self.table = self.dynamodb.Table(self.table_name)
                return True
            
            # Create new table
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'customer_id', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'session_timestamp', 'KeyType': 'RANGE'}  # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'customer_id', 'AttributeType': 'S'},
                    {'AttributeName': 'session_timestamp', 'AttributeType': 'N'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Project', 'Value': 'CustomerAnalytics'},
                    {'Key': 'Environment', 'Value': 'Development'},
                    {'Key': 'CostCenter', 'Value': 'FreeTier'}
                ]
            )
            
            # Wait for table to be created
            print("Waiting for table to become active...")
            self.table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
            
            print(f"SUCCESS: Table {self.table_name} created")
            return True
            
        except ClientError as e:
            print(f"ERROR creating table: {e}")
            return False

    def insert_sample_data(self):
        """Insert sample customer behavior data"""
        
        print("\nInserting sample behavior data...")
        
        # Products list for behavior tracking
        products = [f'PROD{i:03d}' for i in range(1, 21)]
        
        # Actions that customers can take
        actions = ['browse', 'search', 'view_product', 'add_to_cart', 
                  'remove_from_cart', 'start_checkout', 'complete_purchase']
        
        # Device types
        devices = ['mobile', 'desktop', 'tablet']
        
        # Generate behavior records
        records = []
        items_added = 0
        
        with self.table.batch_writer() as batch:
            for customer_num in range(1, 101):  # 100 customers
                customer_id = f'CUST{customer_num:04d}'
                
                # Generate 2-5 sessions per customer
                num_sessions = random.randint(2, 5)
                
                for session_num in range(num_sessions):
                    # Random timestamp within last 30 days
                    days_ago = random.randint(0, 30)
                    hours_ago = random.randint(0, 23)
                    timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
                    timestamp_epoch = int(timestamp.timestamp())
                    
                    # Session details
                    session_duration = random.randint(30, 1800)  # 30 seconds to 30 minutes
                    pages_viewed = random.randint(1, 15)
                    products_viewed = random.sample(products, k=random.randint(1, min(5, len(products))))
                    
                    # Determine if customer converted
                    converted = random.random() > 0.7  # 30% conversion rate
                    
                    # Cart value
                    if converted:
                        cart_value = Decimal(str(round(random.uniform(50, 500), 2)))
                    else:
                        cart_value = Decimal('0') if random.random() > 0.5 else Decimal(str(round(random.uniform(10, 200), 2)))
                    
                    # User actions in session
                    session_actions = random.sample(actions, k=random.randint(1, min(4, len(actions))))
                    
                    item = {
                        'customer_id': customer_id,
                        'session_timestamp': timestamp_epoch,
                        'session_id': f'SESSION{timestamp_epoch}{customer_num:04d}',
                        'session_date': timestamp.strftime('%Y-%m-%d'),
                        'session_duration_seconds': session_duration,
                        'pages_viewed': pages_viewed,
                        'products_viewed': products_viewed,
                        'actions': session_actions,
                        'device_type': random.choice(devices),
                        'converted': converted,
                        'cart_value': cart_value,
                        'referrer': random.choice(['google', 'facebook', 'instagram', 'direct', 'email']),
                        'browser': random.choice(['Chrome', 'Safari', 'Firefox', 'Edge'])
                    }
                    
                    batch.put_item(Item=item)
                    items_added += 1
                    
                    if items_added % 50 == 0:
                        print(f"  Added {items_added} records...")
        
        print(f"SUCCESS: Added {items_added} behavior records")
        return items_added

    def query_sample_data(self):
        """Run sample queries to verify data"""
        
        print("\nRunning sample queries...")
        
        # Query 1: Get all sessions for a specific customer
        customer_id = 'CUST0001'
        response = self.table.query(
            KeyConditionExpression='customer_id = :cid',
            ExpressionAttributeValues={':cid': customer_id}
        )
        print(f"\n1. Sessions for {customer_id}: {response['Count']} found")
        
        # Query 2: Get recent sessions (using scan - use sparingly)
        current_timestamp = int(datetime.now().timestamp())
        week_ago = current_timestamp - (7 * 24 * 3600)
        
        response = self.table.scan(
            FilterExpression='session_timestamp > :ts',
            ExpressionAttributeValues={':ts': week_ago},
            Limit=10
        )
        print(f"2. Recent sessions (last week): {response['Count']} found (limited to 10)")
        
        # Query 3: Calculate metrics
        total_items = 0
        total_conversions = 0
        total_revenue = Decimal('0')
        
        # Sample scan for metrics (in production, use Streams + Lambda for aggregation)
        scan_kwargs = {'Limit': 100}
        response = self.table.scan(**scan_kwargs)
        for item in response['Items']:
            total_items += 1
            if item.get('converted'):
                total_conversions += 1
            total_revenue += item.get('cart_value', Decimal('0'))
        
        if total_items > 0:
            conversion_rate = (total_conversions / total_items) * 100
            avg_cart_value = total_revenue / total_items
            print(f"\n3. Sample Metrics (first 100 records):")
            print(f"   - Conversion rate: {conversion_rate:.1f}%")
            print(f"   - Average cart value: ${avg_cart_value:.2f}")
            print(f"   - Total revenue: ${total_revenue:.2f}")
    
    def check_table_size(self):
        """Check table size and item count"""
        
        print("\nChecking table metrics...")
        
        try:
            response = self.client.describe_table(TableName=self.table_name)
            table_info = response['Table']
            
            item_count = table_info.get('ItemCount', 0)
            table_size_bytes = table_info.get('TableSizeBytes', 0)
            table_size_mb = table_size_bytes / (1024 * 1024)
            
            # Free tier is 25GB
            free_tier_gb = 25
            usage_percent = (table_size_mb / 1024) / free_tier_gb * 100
            
            print(f"Table: {self.table_name}")
            print(f"Items: {item_count}")
            print(f"Size: {table_size_mb:.2f} MB")
            print(f"Free tier usage: {usage_percent:.3f}% of 25GB")
            
            if usage_percent > 80:
                print("WARNING: Approaching free tier limit!")
            
            return table_size_mb
            
        except ClientError as e:
            print(f"ERROR checking table size: {e}")
            return 0

    def save_config(self):
        """Save DynamoDB configuration"""
        
        config = {
            'table_name': self.table_name,
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'created_at': datetime.now().isoformat(),
            'key_schema': {
                'partition_key': 'customer_id',
                'sort_key': 'session_timestamp'
            }
        }
        
        config_path = Path('config/aws/dynamodb_config.json')
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\nConfiguration saved to: {config_path}")
        
        # Update .env file
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update or add DYNAMODB_TABLE
            found = False
            for i, line in enumerate(lines):
                if line.startswith('DYNAMODB_TABLE='):
                    lines[i] = f'DYNAMODB_TABLE={self.table_name}\n'
                    found = True
                    break
            
            if not found:
                lines.append(f'DYNAMODB_TABLE={self.table_name}\n')
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            print(f"Updated .env with DYNAMODB_TABLE={self.table_name}")
    
    def create_global_secondary_index(self):
        """Create GSI for querying by device type (example)"""
        
        print("\nCreating Global Secondary Index...")
        
        try:
            self.client.update_table(
                TableName=self.table_name,
                AttributeDefinitions=[
                    {'AttributeName': 'device_type', 'AttributeType': 'S'},
                    {'AttributeName': 'session_timestamp', 'AttributeType': 'N'}
                ],
                GlobalSecondaryIndexUpdates=[{
                    'Create': {
                        'IndexName': 'device-type-index',
                        'KeySchema': [
                            {'AttributeName': 'device_type', 'KeyType': 'HASH'},
                            {'AttributeName': 'session_timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 1,
                            'WriteCapacityUnits': 1
                        }
                    }
                }]
            )
            print("GSI creation initiated (will take a few minutes)")
            
        except ClientError as e:
            if 'ValidationException' in str(e):
                print("Note: GSI requires provisioned capacity mode. Skipping for on-demand mode.")
            else:
                print(f"ERROR creating GSI: {e}")

def main():
    print("="*50)
    print("AWS DynamoDB Setup for Customer Analytics Platform")
    print("="*50)
    
    manager = DynamoDBManager()
    
    # Create table
    if not manager.create_behavior_table():
        print("Failed to create DynamoDB table")
        sys.exit(1)
    
    # Insert sample data
    items_count = manager.insert_sample_data()
    
    # Run sample queries
    manager.query_sample_data()
    
    # Check table size
    manager.check_table_size()
    
    # Save configuration
    manager.save_config()
    
    # Note about GSI
    # manager.create_global_secondary_index()
    
    print("\n" + "="*50)
    print("DynamoDB Setup Complete!")
    print(f"Table: {manager.table_name}")
    print(f"Items added: {items_count}")
    print("\nNext steps:")
    print("1. Deploy Lambda functions: python scripts/aws_lambda_setup.py")
    print("2. Set up Athena queries: python scripts/aws_athena_setup.py")
    print("="*50)

if __name__ == "__main__":
    main()
