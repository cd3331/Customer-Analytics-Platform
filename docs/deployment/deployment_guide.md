# Deployment Guide

## Overview

This guide walks through deploying the Customer Analytics Platform from development to production, including security hardening, cost optimization, and monitoring setup.

## Prerequisites

Before deploying to production, ensure you have:

- [x] Tested all components in development
- [x] AWS account with appropriate permissions
- [x] Domain name (optional, for custom API domain)
- [x] SSL/TLS certificate (optional, for HTTPS)
- [x] Budget approval and cost alerts configured

## Deployment Checklist

### Phase 1: Environment Setup

#### 1.1 Create Production AWS Account (Recommended)

For production workloads, use a separate AWS account:

```bash
# Configure production profile
aws configure --profile production
```

#### 1.2 Set Up Environment Variables

Create `.env.production`:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=<production-key>
AWS_SECRET_ACCESS_KEY=<production-secret>
AWS_DEFAULT_REGION=us-east-1
AWS_ACCOUNT_ID=<production-account-id>

# Database Configuration
DB_HOST=<production-rds-endpoint>
DB_USER=admin
DB_PASSWORD=<strong-password>
DB_NAME=customer_analytics_prod

# API Configuration
API_STAGE=prod
API_THROTTLE_RATE=1000
API_THROTTLE_BURST=2000

# Monitoring
CLOUDWATCH_ALARM_EMAIL=alerts@yourcompany.com
COST_ALERT_THRESHOLD=100.00
```

**Security Note:** Never commit `.env.production` to version control!

### Phase 2: Infrastructure Deployment

#### 2.1 Deploy S3 Data Lake

```bash
# Create production S3 bucket with versioning and encryption
python scripts/aws_s3_setup.py --environment production
```

Configuration options:
- Bucket name: `customer-analytics-prod-{timestamp}`
- Versioning: Enabled
- Encryption: AES-256 (default) or KMS
- Lifecycle policies: Archive to Glacier after 90 days
- Access logging: Enabled

#### 2.2 Deploy RDS Database

```bash
# Create production RDS instance
python scripts/aws_rds_setup.py --environment production --instance-class db.t3.small
```

Production settings:
- Instance class: `db.t3.small` (minimum for production)
- Multi-AZ: Enabled (for high availability)
- Automated backups: 7-day retention
- Backup window: 03:00-04:00 UTC
- Maintenance window: Sun:04:00-Sun:05:00 UTC
- Storage: 100 GB with auto-scaling enabled

#### 2.3 Deploy DynamoDB Tables

```bash
# Create production DynamoDB tables
python scripts/aws_dynamodb_setup.py --environment production --billing-mode PAY_PER_REQUEST
```

Production settings:
- Billing mode: On-Demand (recommended) or Provisioned
- Point-in-time recovery: Enabled
- Encryption: Enabled (AWS owned CMK or KMS)
- Streams: Enabled (for change data capture)

#### 2.4 Deploy Lambda Functions

```bash
# Deploy Lambda functions with production configuration
python scripts/aws_lambda_setup.py --environment production
```

Production settings:
- Memory: 512 MB (increase as needed)
- Timeout: 60 seconds
- Reserved concurrency: 10 (prevents runaway costs)
- VPC: Configure if RDS is in VPC
- Environment variables: From `.env.production`
- Dead letter queue: Enabled (SNS topic)

### Phase 3: Security Hardening

#### 3.1 Enable Encryption

**S3 Bucket Encryption:**
```bash
aws s3api put-bucket-encryption \
  --bucket customer-analytics-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

**RDS Encryption:**
- Enable encryption at rest during creation
- Cannot be enabled after creation
- Use KMS for encryption key management

**DynamoDB Encryption:**
```bash
aws dynamodb update-table \
  --table-name customer-behavior-events-prod \
  --sse-specification Enabled=true,SSEType=KMS
```

#### 3.2 Configure IAM Roles

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::customer-analytics-prod/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/customer-behavior-events-prod"
    }
  ]
}
```

#### 3.3 Enable API Authentication

**API Gateway with API Keys:**
```bash
# Create API key
aws apigateway create-api-key \
  --name customer-analytics-prod-key \
  --enabled

# Create usage plan
aws apigateway create-usage-plan \
  --name customer-analytics-prod-plan \
  --throttle burstLimit=2000,rateLimit=1000 \
  --quota limit=1000000,period=MONTH
```

**Alternative: AWS IAM Authentication**
- More secure for AWS-to-AWS communication
- Requires SigV4 signing of requests
- No API keys to manage

#### 3.4 Configure VPC (Optional but Recommended)

For enhanced security, deploy Lambda and RDS in VPC:

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create private subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24

# Configure NAT Gateway for Lambda internet access
# Configure VPC endpoints for S3 and DynamoDB (no data transfer charges)
```

### Phase 4: Monitoring & Alerting

#### 4.1 CloudWatch Alarms

**Lambda Error Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-errors-prod \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=customer-analytics-api-prod \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

**RDS CPU Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name rds-cpu-high-prod \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=customer-analytics-db-prod
```

**Cost Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name monthly-cost-alert \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

#### 4.2 Enable CloudWatch Logs Insights

Configure log retention and enable insights:

```bash
# Set log retention to 30 days (production)
aws logs put-retention-policy \
  --log-group-name /aws/lambda/customer-analytics-api-prod \
  --retention-in-days 30
```

Sample queries for Logs Insights:

**Lambda Errors:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

**API Performance:**
```
fields @timestamp, @duration
| stats avg(@duration), max(@duration), min(@duration)
| sort @timestamp desc
```

#### 4.3 Enable X-Ray Tracing (Optional)

For distributed tracing:

```bash
# Enable X-Ray for Lambda
aws lambda update-function-configuration \
  --function-name customer-analytics-api-prod \
  --tracing-config Mode=Active
```

### Phase 5: Performance Optimization

#### 5.1 Lambda Optimization

- **Provisioned Concurrency:** Pre-warm Lambda instances for consistent performance
- **Lambda Layers:** Extract common dependencies to reduce deployment size
- **Memory Tuning:** Test with different memory settings (more memory = faster CPU)

#### 5.2 Database Optimization

**RDS:**
- Enable Performance Insights
- Configure read replicas for read-heavy workloads
- Optimize queries with indexes

**DynamoDB:**
- Use DAX (DynamoDB Accelerator) for caching
- Configure auto-scaling for provisioned capacity
- Optimize partition key design

#### 5.3 API Optimization

- Enable API Gateway caching (60 second TTL)
- Use CloudFront CDN for global distribution
- Implement response compression

### Phase 6: Backup & Disaster Recovery

#### 6.1 Automated Backups

**S3:**
- Versioning: Enabled
- Cross-region replication: To `us-west-2` (optional)
- Lifecycle policy: Transition to Glacier after 90 days

**RDS:**
- Automated daily backups: 7-day retention
- Manual snapshots: Before major changes
- Cross-region snapshot copy: Enabled

**DynamoDB:**
- Point-in-time recovery: 35-day retention
- On-demand backups: Weekly
- Cross-region backup: AWS Backup

#### 6.2 Disaster Recovery Plan

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 1 hour

**Runbook:**
1. Restore RDS from latest snapshot
2. Restore DynamoDB from point-in-time recovery
3. Restore S3 from versioning or replication
4. Redeploy Lambda functions from version control
5. Update DNS/API Gateway endpoints
6. Verify data integrity

### Phase 7: CI/CD Pipeline (Future)

**GitHub Actions Workflow:**

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Run tests
        run: pytest
      - name: Deploy Lambda
        run: python scripts/aws_lambda_setup.py --environment production
```

## Post-Deployment Verification

### Smoke Tests

```bash
# Test API health
curl https://api.yourcompany.com/health

# Test customer endpoint
curl https://api.yourcompany.com/customer?customer_id=CUST0001

# Test metrics endpoint
curl https://api.yourcompany.com/metrics
```

### Performance Tests

```bash
# Load test with Apache Bench
ab -n 1000 -c 10 https://api.yourcompany.com/metrics

# Expected results:
# - Requests per second: > 100
# - Mean response time: < 100ms
# - Error rate: < 0.1%
```

## Rollback Procedure

If deployment fails:

1. **Revert Lambda:** Deploy previous version
   ```bash
   aws lambda update-function-code \
     --function-name customer-analytics-api-prod \
     --s3-bucket lambda-deployments \
     --s3-key previous-version.zip
   ```

2. **Revert Database:** Restore from snapshot
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier customer-analytics-db-prod \
     --db-snapshot-identifier pre-deployment-snapshot
   ```

3. **Notify stakeholders** via email/Slack

## Cost Estimates

### Development (Free Tier)
- **Monthly cost:** $0-5

### Production (Small Scale)
- **RDS db.t3.small:** $25/month
- **Lambda (1M requests):** $0.20/month
- **DynamoDB (on-demand):** $10/month
- **S3 (100 GB):** $2.30/month
- **Data Transfer:** $5/month
- **CloudWatch:** $3/month
- **Total:** ~$45-50/month

### Production (Medium Scale)
- **RDS db.t3.medium + Multi-AZ:** $120/month
- **Lambda (10M requests):** $2/month
- **DynamoDB (on-demand):** $50/month
- **S3 (1 TB):** $23/month
- **CloudFront:** $20/month
- **Total:** ~$215-250/month

## Maintenance Schedule

- **Daily:** Monitor CloudWatch alarms
- **Weekly:** Review cost reports
- **Monthly:** Apply security patches, review access logs
- **Quarterly:** Performance testing, capacity planning
- **Annually:** Disaster recovery drill, architecture review

## Support Contacts

- **DevOps Lead:** devops@yourcompany.com
- **AWS Support:** https://console.aws.amazon.com/support/
- **On-call:** PagerDuty integration

---

**Last Updated:** 2024-01-15
**Version:** 1.0
**Author:** Chandra Dunn
