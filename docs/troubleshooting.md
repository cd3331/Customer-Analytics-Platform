# Troubleshooting Guide

## Table of Contents
- [Installation Issues](#installation-issues)
- [AWS Connection Problems](#aws-connection-problems)
- [Data Generation Issues](#data-generation-issues)
- [Alteryx Workflow Problems](#alteryx-workflow-problems)
- [Lambda Function Errors](#lambda-function-errors)
- [Database Connection Issues](#database-connection-issues)
- [Dashboard Problems](#dashboard-problems)
- [Cost and Free Tier Issues](#cost-and-free-tier-issues)

---

## Installation Issues

### Problem: pip install fails with dependency conflicts

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
1. Ensure you're using Python 3.8 or higher:
   ```bash
   python --version
   ```

2. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

3. Install in a fresh virtual environment:
   ```bash
   deactivate  # if already in a venv
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Problem: Virtual environment not activating

**Symptoms:**
- Command not found
- Wrong Python version after activation

**Solutions:**

**On Windows:**
```bash
venv\Scripts\activate
```

**On Linux/Mac:**
```bash
source venv/bin/activate
```

**Using PowerShell (Windows):**
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## AWS Connection Problems

### Problem: NoCredentialsError when running AWS scripts

**Symptoms:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solutions:**

1. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Verify .env contains AWS credentials:**
   ```bash
   cat .env
   ```
   Should contain:
   ```
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_DEFAULT_REGION=us-east-1
   ```

3. **Ensure .env is being loaded:**
   Add this at the start of your script:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv('AWS_ACCESS_KEY_ID'))  # Should not be None
   ```

4. **Alternative: Use AWS CLI credentials:**
   ```bash
   aws configure
   ```

### Problem: Access Denied errors

**Symptoms:**
```
botocore.exceptions.ClientError: An error occurred (AccessDenied)
```

**Solutions:**

1. **Verify IAM permissions:** Your AWS user needs these policies:
   - AmazonS3FullAccess
   - AmazonRDSFullAccess
   - AmazonDynamoDBFullAccess
   - AWSLambda_FullAccess

2. **Check if MFA is required:**
   - Some accounts require MFA tokens for API access
   - Use temporary credentials with STS if needed

3. **Verify region settings:**
   ```python
   # Ensure region is set correctly
   AWS_DEFAULT_REGION=us-east-1
   ```

### Problem: Free Tier limits exceeded

**Symptoms:**
```
Error: Request limit exceeded
Charges appearing in billing dashboard
```

**Solutions:**

1. **Check current usage:**
   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=2024-01-01,End=2024-01-31 \
     --granularity MONTHLY \
     --metrics "BlendedCost"
   ```

2. **Enable billing alerts:**
   - AWS Console → Billing → Preferences
   - Enable "Receive Billing Alerts"
   - Set up CloudWatch alarm for $5 threshold

3. **Shut down resources:**
   ```bash
   # Stop RDS instance
   aws rds stop-db-instance --db-instance-identifier customer-analytics-db

   # Delete Lambda functions
   aws lambda delete-function --function-name customer-analytics-api
   ```

---

## Data Generation Issues

### Problem: generate_sample_data.py fails

**Symptoms:**
```
ModuleNotFoundError: No module named 'faker'
```

**Solutions:**

1. **Install missing dependencies:**
   ```bash
   pip install faker pandas numpy
   ```

2. **Verify data directory exists:**
   ```bash
   mkdir -p data/sample
   ```

3. **Run with verbose output:**
   ```bash
   python scripts/data-generation/generate_sample_data.py
   ```

### Problem: Generated data has incorrect format

**Symptoms:**
- CSV files missing columns
- Date formats incorrect
- Empty files

**Solutions:**

1. **Delete and regenerate:**
   ```bash
   rm -rf data/sample/*
   python scripts/data-generation/generate_sample_data.py
   ```

2. **Check generation_summary.json:**
   ```bash
   cat data/sample/generation_summary.json
   ```
   Should show non-zero counts for all datasets.

---

## Alteryx Workflow Problems

### Problem: Cannot connect to AWS data sources

**Symptoms:**
- Connection test fails
- "Invalid credentials" error

**Solutions:**

1. **Use long-term credentials:** Create IAM user with Access Keys (not temporary credentials)

2. **Test AWS connection outside Alteryx:**
   ```python
   import boto3
   s3 = boto3.client('s3')
   print(s3.list_buckets())
   ```

3. **Configure Alteryx AWS connection:**
   - Use "Static Credentials" not "Profile"
   - Enter Access Key ID and Secret Access Key directly
   - Test connection before saving

### Problem: Workflow runs but produces no output

**Symptoms:**
- Workflow completes successfully
- No files in output folder
- Empty result sets

**Solutions:**

1. **Enable Browse tools:** Add Browse tools after each step to inspect data

2. **Check data exists in inputs:**
   - Verify S3 bucket has data files
   - Verify RDS tables are populated
   - Check file paths are correct

3. **Review workflow configuration:**
   - Output path is writable
   - All connections are valid
   - Joins are not filtering out all records

### Problem: Formula tool errors

**Symptoms:**
```
Error: Invalid formula syntax
```

**Solutions:**

1. **Check formula syntax:**
   ```
   Correct:   IF [days_since_transaction] > 90 THEN 1 ELSE 0 ENDIF
   Incorrect: IF [days_since_transaction] > 90 THEN 1 ELSE 0
   ```

2. **Verify field names match exactly:** Use Browse tool to see actual field names

3. **Use IF-ELSEIF-ELSE for multi-condition:**
   ```
   IF [days] > 180 THEN "High"
   ELSEIF [days] > 90 THEN "Medium"
   ELSE "Low"
   ENDIF
   ```

---

## Lambda Function Errors

### Problem: Lambda function times out

**Symptoms:**
```
Task timed out after 30.00 seconds
```

**Solutions:**

1. **Increase timeout in lambda_config.json:**
   ```json
   {
     "timeout": 60
   }
   ```

2. **Optimize code:**
   - Use pagination for large DynamoDB scans
   - Limit S3 object size
   - Add early returns

3. **Check CloudWatch Logs:**
   ```bash
   aws logs tail /aws/lambda/customer-analytics-api --follow
   ```

### Problem: Lambda returns 500 error

**Symptoms:**
```json
{
  "statusCode": 500,
  "body": "{\"error\": \"...\"}"
}
```

**Solutions:**

1. **Check CloudWatch Logs for stack trace:**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/customer-analytics-api \
     --filter-pattern "ERROR"
   ```

2. **Common issues:**
   - Missing environment variables (DYNAMODB_TABLE)
   - IAM role lacks permissions
   - Malformed JSON in request

3. **Test locally:**
   ```bash
   python scripts/test_lambda.py
   ```

### Problem: Cannot invoke Lambda function

**Symptoms:**
```
An error occurred (ResourceNotFoundException) when calling the Invoke operation
```

**Solutions:**

1. **Verify function exists:**
   ```bash
   aws lambda list-functions | grep customer-analytics
   ```

2. **Check function name matches exactly:**
   - Function name: `customer-analytics-api`
   - Not: `customer_analytics_api` or `CustomerAnalyticsAPI`

3. **Verify region:**
   ```bash
   aws lambda get-function --function-name customer-analytics-api --region us-east-1
   ```

---

## Database Connection Issues

### Problem: Cannot connect to RDS MySQL

**Symptoms:**
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solutions:**

1. **Check RDS instance is running:**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier customer-analytics-db \
     --query 'DBInstances[0].DBInstanceStatus'
   ```

2. **Verify security group allows your IP:**
   - RDS Console → Security Groups
   - Add inbound rule: Type=MySQL, Source=Your IP

3. **Test connection with mysql client:**
   ```bash
   mysql -h your-rds-endpoint.rds.amazonaws.com -u admin -p
   ```

4. **Check endpoint in .env:**
   ```bash
   grep DB_HOST .env
   ```

### Problem: DynamoDB table not found

**Symptoms:**
```
botocore.exceptions.ClientError: An error occurred (ResourceNotFoundException)
```

**Solutions:**

1. **List existing tables:**
   ```bash
   aws dynamodb list-tables
   ```

2. **Create table if missing:**
   ```bash
   python scripts/aws_dynamodb_setup.py
   ```

3. **Verify table name matches code:**
   - Code expects: `customer-behavior-events`
   - Not: `customer_behavior_events`

---

## Dashboard Problems

### Problem: Power BI cannot refresh data

**Symptoms:**
- "Data source error"
- "Unable to connect"

**Solutions:**

1. **For S3 data source:**
   - Use AWS S3 connector (not Web)
   - Provide Access Key and Secret Key
   - Use full S3 URL: `s3://bucket-name/path/file.csv`

2. **For MySQL data source:**
   - Install MySQL ODBC driver
   - Use server name (RDS endpoint), not IP
   - Test connection with "Test Connection" button

3. **Refresh credentials:**
   - File → Options → Data source settings
   - Edit credentials for each source

### Problem: Web dashboard shows no data

**Symptoms:**
- Dashboard loads but shows "No data available"

**Solutions:**

1. **Check API endpoint is reachable:**
   ```bash
   curl https://your-api-gateway-url/metrics
   ```

2. **Verify Lambda has data to return:**
   - Check DynamoDB table has items
   - Check S3 bucket has processed files

3. **Check browser console for errors:**
   - Open Developer Tools (F12)
   - Look for CORS errors or 403/500 responses

---

## Cost and Free Tier Issues

### Problem: Unexpected charges appearing

**Symptoms:**
- Billing dashboard shows charges
- Free tier usage exceeded

**Solutions:**

1. **Review Cost Explorer:**
   - AWS Console → Cost Management → Cost Explorer
   - Group by: Service
   - Identify which service is charging

2. **Common charge sources:**
   - RDS instance running 24/7 (stop when not in use)
   - S3 storage over 5GB
   - Data transfer out (use CloudFront)
   - Lambda beyond 1M requests

3. **Set up billing alerts:**
   ```bash
   python scripts/monitoring/cost_monitor.py --alert --threshold 4.00
   ```

### Problem: RDS exceeding free tier hours

**Symptoms:**
- Charges for RDS even with t3.micro

**Solutions:**

1. **Stop RDS when not in use:**
   ```bash
   aws rds stop-db-instance --db-instance-identifier customer-analytics-db
   ```

2. **Create start/stop schedule:**
   - Use EventBridge rule to stop at night
   - Use Lambda to stop on weekends

3. **Monitor hours usage:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/RDS \
     --metric-name DatabaseConnections \
     --dimensions Name=DBInstanceIdentifier,Value=customer-analytics-db \
     --start-time 2024-01-01T00:00:00Z \
     --end-time 2024-01-31T23:59:59Z \
     --period 86400 \
     --statistics Sum
   ```

---

## General Debugging Tips

### Enable Verbose Logging

Add to Python scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Environment Variables

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.environ)"
```

### Verify AWS Region Consistency

All services should be in the same region (recommended: us-east-1)

### Use AWS CLI for Testing

Before running Python scripts, test with AWS CLI:
```bash
aws s3 ls
aws rds describe-db-instances
aws dynamodb list-tables
aws lambda list-functions
```

---

## Getting Additional Help

### Check Logs
1. **Python script errors:** Terminal output
2. **Lambda errors:** CloudWatch Logs
3. **RDS errors:** RDS Console → Logs
4. **S3 errors:** S3 Access Logs (if enabled)

### Community Resources
- AWS Free Tier FAQ: https://aws.amazon.com/free/free-tier-faqs/
- Alteryx Community: https://community.alteryx.com/
- Power BI Community: https://community.powerbi.com/

### Contact Support
For project-specific issues:
- GitHub Issues: https://github.com/your-username/customer-analytics-platform/issues
- Email: cd3331github@gmail.com

---

## Appendix: Error Code Reference

| Error Code | Service | Meaning | Solution |
|------------|---------|---------|----------|
| NoCredentialsError | AWS | No AWS credentials found | Set up .env or aws configure |
| AccessDenied | AWS | Insufficient IAM permissions | Add required IAM policies |
| ResourceNotFoundException | Lambda/DynamoDB | Resource doesn't exist | Create resource using setup script |
| ValidationException | DynamoDB | Invalid parameter | Check table schema matches code |
| 2003 | MySQL | Can't connect to server | Check RDS running and security group |
| 500 | Lambda | Internal server error | Check CloudWatch Logs |
| 403 | API Gateway | Forbidden | Check API key or IAM auth |
| 429 | Any AWS | Rate limit exceeded | Implement exponential backoff |
