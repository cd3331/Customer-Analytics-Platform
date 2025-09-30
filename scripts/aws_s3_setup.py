#!/usr/bin/env python3
"""
AWS S3 Setup Script
Creates S3 bucket and uploads sample data
Monitors free tier usage
"""

import os
import sys
import boto3
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

# Load environment variables
load_dotenv()

class S3Manager:
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.bucket_name = None
            print("AWS S3 client initialized successfully")
        except NoCredentialsError:
            print("ERROR: AWS credentials not found. Please check your .env file")
            sys.exit(1)

    def create_bucket(self):
        """Create S3 bucket with proper configuration"""
        timestamp = datetime.now().strftime('%Y%m%d')
        self.bucket_name = f"customer-analytics-{timestamp}-{os.getenv('AWS_ACCOUNT_ID', 'demo')[-4:]}"

        print(f"\nCreating S3 bucket: {self.bucket_name}")
        try:
            if os.getenv('AWS_REGION', 'us-east-1') == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': os.getenv('AWS_REGION')}
                )
            print(f"SUCCESS: Bucket {self.bucket_name} created")

            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            print("Versioning enabled")

            self.s3_client.put_bucket_tagging(
                Bucket=self.bucket_name,
                Tagging={'TagSet': [
                    {'Key': 'Project', 'Value': 'CustomerAnalytics'},
                    {'Key': 'Environment', 'Value': 'Development'},
                    {'Key': 'CostCenter', 'Value': 'FreeTier'}
                ]}
            )
            print("Tags added for cost tracking")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"Bucket {self.bucket_name} already exists and you own it")
                return True
            elif e.response['Error']['Code'] == 'BucketAlreadyExists':
                print(f"ERROR: Bucket name {self.bucket_name} already taken globally")
                print("Trying alternative name...")
                import random
                self.bucket_name = f"{self.bucket_name}-{random.randint(1000,9999)}"
                return self.create_bucket()
            else:
                print(f"ERROR: {e}")
                return False

    def upload_sample_data(self):
        """Upload sample data from local data/sample directory"""
        sample_dir = Path("data/sample")
        if not sample_dir.exists():
            print("ERROR: data/sample directory not found")
            print("Run 'python scripts/data-generation/generate_sample_data.py' first")
            return False

        files_uploaded = 0
        total_size = 0
        print(f"\nUploading files from {sample_dir} to s3://{self.bucket_name}/data/")

        for file_path in sample_dir.glob("*.csv"):
            file_size = file_path.stat().st_size
            s3_key = f"data/{file_path.name}"
            try:
                print(f"Uploading {file_path.name} ({file_size/1024:.1f} KB)...", end="")
                self.s3_client.upload_file(
                    str(file_path),
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': 'text/csv',
                        'Metadata': {
                            'uploaded_at': datetime.now().isoformat(),
                            'source': 'sample_data_generator'
                        }
                    }
                )
                print(" SUCCESS")
                files_uploaded += 1
                total_size += file_size
            except ClientError as e:
                print(f" FAILED: {e}")

        print(f"\nSummary:\nFiles uploaded: {files_uploaded}\nTotal size: {total_size/1024:.2f} KB")
        print(f"S3 location: s3://{self.bucket_name}/data/")
        return files_uploaded > 0

    def check_bucket_size(self):
        """Check current bucket size against free tier limit"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            total_size = 0
            file_count = 0
            if 'Contents' in response:
                for obj in response['Contents']:
                    total_size += obj['Size']
                    file_count += 1

            free_tier_limit_gb = 5
            size_gb = total_size / (1024**3)
            usage_percent = (size_gb / free_tier_limit_gb) * 100

            print(f"\nS3 Storage Usage:\nFiles: {file_count}\nTotal size: {size_gb:.4f} GB")
            print(f"Free tier limit: {free_tier_limit_gb} GB\nUsage: {usage_percent:.1f}%")
            if usage_percent > 80:
                print("WARNING: Approaching free tier limit!")
            return size_gb
        except ClientError as e:
            print(f"ERROR checking bucket size: {e}")
            return 0

    def create_folder_structure(self):
        """Create organized folder structure in S3"""
        folders = ['data/', 'data/raw/', 'data/processed/', 'data/archive/',
                   'models/', 'reports/', 'logs/']
        print("\nCreating folder structure...")
        for folder in folders:
            try:
                self.s3_client.put_object(Bucket=self.bucket_name, Key=folder)
                print(f"Created: {folder}")
            except ClientError as e:
                print(f"ERROR creating {folder}: {e}")

    def save_config(self):
        """Save bucket configuration for other scripts"""
        config = {
            'bucket_name': self.bucket_name,
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'created_at': datetime.now().isoformat(),
            'data_prefix': 'data/',
            'free_tier_limit_gb': 5
        }
        config_path = Path('config/aws/s3_config.json')
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {config_path}")

        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if line.startswith('S3_BUCKET_NAME='):
                    lines[i] = f'S3_BUCKET_NAME={self.bucket_name}\n'
                    found = True
                    break
            if not found:
                lines.append(f'\nS3_BUCKET_NAME={self.bucket_name}\n')
            with open(env_path, 'w') as f:
                f.writelines(lines)
            print(f"Updated .env with S3_BUCKET_NAME={self.bucket_name}")

    def test_access(self):
        """Test read/write access to bucket"""
        print("\nTesting bucket access...")
        test_key = 'test/test_file.txt'
        test_content = f'Test upload at {datetime.now().isoformat()}'
        try:
            self.s3_client.put_object(Bucket=self.bucket_name, Key=test_key, Body=test_content.encode('utf-8'))
            print("Write test: SUCCESS")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=test_key)
            content = response['Body'].read().decode('utf-8')
            print("Read test: SUCCESS")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            return True
        except ClientError as e:
            print(f"Access test FAILED: {e}")
            return False

def main():
    print("="*50)
    print("AWS S3 Setup for Customer Analytics Platform")
    print("="*50)

    if not Path("data/sample/customers.csv").exists():
        print("\nERROR: Sample data not found!")
        print("Please run: python scripts/data-generation/generate_sample_data.py")
        sys.exit(1)

    s3_manager = S3Manager()
    if not s3_manager.create_bucket():
        print("Failed to create bucket. Exiting.")
        sys.exit(1)

    s3_manager.create_folder_structure()

    if not s3_manager.upload_sample_data():
        print("Failed to upload data. Exiting.")
        sys.exit(1)

    s3_manager.test_access()
    s3_manager.check_bucket_size()
    s3_manager.save_config()

    print("\n" + "="*50)
    print("S3 Setup Complete!")
    print(f"Bucket: {s3_manager.bucket_name}")
    print("Next steps:")
    print("1. Set up RDS database: python scripts/aws_rds_setup.py")
    print("2. Set up DynamoDB: python scripts/aws_dynamodb_setup.py")
    print("3. Deploy Lambda functions: python scripts/aws_lambda_setup.py")
    print("="*50)

if __name__ == "__main__":
    main()
