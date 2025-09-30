#!/usr/bin/env python3
"""
AWS RDS Setup Script
Creates RDS MySQL instance within free tier limits
Sets up marketing database with sample data
"""

import os
import sys
import boto3
import pymysql
import time
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

class RDSManager:
    def __init__(self):
        try:
            self.rds_client = boto3.client(
                'rds',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.ec2_client = boto3.client(
                'ec2',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            self.db_instance_id = f"customer-analytics-db-{datetime.now().strftime('%Y%m%d')}"
            self.db_name = 'marketing_db'
            self.master_username = 'admin'
            self.master_password = self.generate_password()
            self.endpoint = None
            
            print("AWS RDS client initialized successfully")
            
        except Exception as e:
            print(f"ERROR initializing RDS client: {e}")
            sys.exit(1)

    def generate_password(self):
        """Generate a secure password for RDS"""
        import string
        import random
        
        chars = string.ascii_letters + string.digits + "!@#%^*"
        password = ''.join(random.choice(chars) for _ in range(16))
        return password
    
    def create_security_group(self):
        """Create security group for RDS access"""
        sg_name = f"rds-sg-{self.db_instance_id}"
        
        try:
            response = self.ec2_client.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [sg_name]}]
            )
            if response['SecurityGroups']:
                sg_id = response['SecurityGroups'][0]['GroupId']
                print(f"Using existing security group: {sg_id}")
                return sg_id
        except ClientError:
            pass
        
        try:
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description='Security group for Customer Analytics RDS'
            )
            sg_id = response['GroupId']
            
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[{
                    'IpProtocol': 'tcp',
                    'FromPort': 3306,
                    'ToPort': 3306,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'MySQL access'}]
                }]
            )
            
            print(f"Created security group: {sg_id}")
            print("WARNING: Security group allows access from anywhere (0.0.0.0/0)")
            print("         Restrict this in production!")
            return sg_id
        except ClientError as e:
            print(f"ERROR creating security group: {e}")
            return None

    def create_rds_instance(self):
        """Create RDS MySQL instance within free tier"""
        
        print(f"\nCreating RDS instance: {self.db_instance_id}")
        print("This will take 5-10 minutes...")
        
        sg_id = self.create_security_group()
        if not sg_id:
            return False
        
        try:
            self.rds_client.create_db_instance(
                DBInstanceIdentifier=self.db_instance_id,
                DBInstanceClass='db.t3.micro',
                Engine='mysql',
                EngineVersion='8.0',
                MasterUsername=self.master_username,
                MasterUserPassword=self.master_password,
                DBName=self.db_name,
                AllocatedStorage=20,
                StorageType='gp2',
                StorageEncrypted=False,
                VpcSecurityGroupIds=[sg_id],
                PubliclyAccessible=True,
                BackupRetentionPeriod=1,
                PreferredBackupWindow='03:00-04:00',
                PreferredMaintenanceWindow='sun:04:00-sun:05:00',
                MultiAZ=False,
                AutoMinorVersionUpgrade=True,
                Tags=[
                    {'Key': 'Project', 'Value': 'CustomerAnalytics'},
                    {'Key': 'Environment', 'Value': 'Development'},
                    {'Key': 'CostCenter', 'Value': 'FreeTier'}
                ]
            )
            print("RDS instance creation initiated")
            print("Waiting for instance to become available...")
            
            waiter = self.rds_client.get_waiter('db_instance_available')
            waiter.wait(
                DBInstanceIdentifier=self.db_instance_id,
                WaiterConfig={'Delay': 30, 'MaxAttempts': 30}
            )
            
            response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier=self.db_instance_id
            )
            db_instance = response['DBInstances'][0]
            self.endpoint = db_instance['Endpoint']['Address']
            port = db_instance['Endpoint']['Port']
            
            print(f"\nSUCCESS: RDS instance created!")
            print(f"Endpoint: {self.endpoint}")
            print(f"Port: {port}")
            return True
        except ClientError as e:
            if 'DBInstanceAlreadyExists' in str(e):
                print(f"Instance {self.db_instance_id} already exists")
                return self.get_existing_instance()
            else:
                print(f"ERROR creating RDS instance: {e}")
                return False
    
    def get_existing_instance(self):
        """Get details of existing RDS instance"""
        try:
            response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier=self.db_instance_id
            )
            if response['DBInstances']:
                db_instance = response['DBInstances'][0]
                self.endpoint = db_instance['Endpoint']['Address']
                print(f"Found existing instance: {self.endpoint}")
                return True
        except ClientError as e:
            print(f"ERROR getting instance details: {e}")
        return False

    def create_tables(self):
        """Create database tables and insert sample data"""
        print("\nConnecting to database...")
        time.sleep(10)
        
        try:
            connection = pymysql.connect(
                host=self.endpoint,
                user=self.master_username,
                password=self.master_password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Connected to database successfully")
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS campaigns (
                        campaign_id INT PRIMARY KEY AUTO_INCREMENT,
                        campaign_name VARCHAR(100) NOT NULL,
                        start_date DATE,
                        end_date DATE,
                        channel VARCHAR(50),
                        budget DECIMAL(10,2),
                        INDEX idx_dates (start_date, end_date)
                    ) ENGINE=InnoDB
                """)
                print("Created campaigns table")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS campaign_responses (
                        response_id INT PRIMARY KEY AUTO_INCREMENT,
                        customer_id VARCHAR(10) NOT NULL,
                        campaign_id INT,
                        response_date DATE,
                        clicked BOOLEAN DEFAULT FALSE,
                        converted BOOLEAN DEFAULT FALSE,
                        revenue DECIMAL(10,2) DEFAULT 0.00,
                        FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
                        INDEX idx_customer (customer_id),
                        INDEX idx_campaign (campaign_id)
                    ) ENGINE=InnoDB
                """)
                print("Created campaign_responses table")
                
                campaigns = [
                    ('Summer Sale 2024', '2024-06-01', '2024-08-31', 'multi', 5000),
                    ('Back to School', '2024-08-15', '2024-09-15', 'social', 3000),
                    ('Black Friday', '2024-11-25', '2024-11-30', 'email', 10000),
                    ('Holiday Season', '2024-12-01', '2024-12-31', 'multi', 15000),
                    ('New Year Promo', '2025-01-01', '2025-01-15', 'email', 2000)
                ]
                cursor.executemany("""
                    INSERT INTO campaigns (campaign_name, start_date, end_date, channel, budget)
                    VALUES (%s, %s, %s, %s, %s)
                """, campaigns)
                print(f"Inserted {len(campaigns)} campaigns")
                
                import random
                responses = []
                for _ in range(300):
                    responses.append((
                        f"CUST{random.randint(1,100):04d}",
                        random.randint(1, 5),
                        f"2024-{random.randint(6,12):02d}-{random.randint(1,28):02d}",
                        random.random() > 0.5,
                        random.random() > 0.7,
                        round(random.uniform(0, 500), 2) if random.random() > 0.7 else 0
                    ))
                cursor.executemany("""
                    INSERT INTO campaign_responses 
                    (customer_id, campaign_id, response_date, clicked, converted, revenue)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, responses)
                print(f"Inserted {len(responses)} campaign responses")
                
                connection.commit()
            connection.close()
            print("Database setup complete")
            return True
        except pymysql.Error as e:
            print(f"ERROR setting up database: {e}")
            return False

    def save_config(self):
        """Save RDS configuration for other scripts"""
        config = {
            'db_instance_id': self.db_instance_id,
            'endpoint': self.endpoint,
            'port': 3306,
            'database': self.db_name,
            'username': self.master_username,
            'password': self.master_password,
            'created_at': datetime.now().isoformat()
        }
        config_path = Path('config/aws/rds_config.json')
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {config_path}")
        
        env_updates = {
            'RDS_HOST': self.endpoint,
            'RDS_PORT': '3306',
            'RDS_DATABASE': self.db_name,
            'RDS_USERNAME': self.master_username,
            'RDS_PASSWORD': self.master_password
        }
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            for key, value in env_updates.items():
                found = False
                for i, line in enumerate(lines):
                    if line.startswith(f'{key}='):
                        lines[i] = f'{key}={value}\n'
                        found = True
                        break
                if not found:
                    lines.append(f'{key}={value}\n')
            with open(env_path, 'w') as f:
                f.writelines(lines)
            print("Updated .env with RDS credentials")
    
    def test_connection(self):
        """Test database connection and run sample query"""
        print("\nTesting database connection...")
        try:
            connection = pymysql.connect(
                host=self.endpoint,
                user=self.master_username,
                password=self.master_password,
                database=self.db_name
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM campaigns")
                result = cursor.fetchone()
                print(f"Campaigns table has {result[0]} records")
                
                cursor.execute("""
                    SELECT c.campaign_name, COUNT(cr.response_id) as responses,
                           SUM(cr.converted) as conversions
                    FROM campaigns c
                    LEFT JOIN campaign_responses cr ON c.campaign_id = cr.campaign_id
                    GROUP BY c.campaign_id
                """)
                print("\nCampaign Performance:")
                for row in cursor.fetchall():
                    print(f"  {row[0]}: {row[1]} responses, {row[2]} conversions")
            connection.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

def main():
    print("="*50)
    print("AWS RDS Setup for Customer Analytics Platform")
    print("="*50)
    
    manager = RDSManager()
    
    if not manager.create_rds_instance():
        print("Failed to create RDS instance")
        sys.exit(1)
    
    if not manager.create_tables():
        print("Failed to set up database")
        print("You may need to wait a few more minutes and retry")
    
    manager.test_connection()
    manager.save_config()
    
    print("\n" + "="*50)
    print("RDS Setup Complete!")
    print(f"Instance: {manager.db_instance_id}")
    print(f"Endpoint: {manager.endpoint}")
    print(f"Database: {manager.db_name}")
    print("\nIMPORTANT: Save these credentials securely!")
    print(f"Username: {manager.master_username}")
    print(f"Password: {manager.master_password}")
    print("\nNext steps:")
    print("1. Set up DynamoDB: python scripts/aws_dynamodb_setup.py")
    print("2. Deploy Lambda functions: python scripts/aws_lambda_setup.py")
    print("="*50)

if __name__ == "__main__":
    main()
