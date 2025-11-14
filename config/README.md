# Configuration Files

## ⚠️ Security Notice

**NEVER commit real credentials to version control!**

The configuration files in this directory are **templates with placeholders**. They are safe to commit to git.

## How to Use Configuration Files

### For Local Development

1. **Copy template files to local versions:**
   ```bash
   cp config/aws/rds_config.json config/aws/rds_config.local.json
   cp config/aws/s3_config.json config/aws/s3_config.local.json
   cp config/alteryx/alteryx_config.json config/alteryx/alteryx_config.local.json
   ```

2. **Edit the `.local.json` files with your real credentials:**
   - These files are automatically ignored by git (see `.gitignore`)
   - Update placeholders like `YOUR_AWS_ACCESS_KEY_ID` with actual values

3. **Update your scripts to use local configs when they exist:**
   ```python
   import json
   import os

   def load_config(config_name):
       # Try to load local config first
       local_path = f"config/aws/{config_name}.local.json"
       template_path = f"config/aws/{config_name}.json"

       if os.path.exists(local_path):
           with open(local_path) as f:
               return json.load(f)
       else:
           with open(template_path) as f:
               return json.load(f)
   ```

### Environment Variables (Recommended)

Instead of storing credentials in config files, use environment variables via `.env`:

```bash
# .env (this file is gitignored)
AWS_ACCESS_KEY_ID=your_real_key
AWS_SECRET_ACCESS_KEY=your_real_secret
RDS_PASSWORD=your_real_password
```

Then load in your code:
```python
from dotenv import load_dotenv
import os

load_dotenv()

aws_key = os.getenv('AWS_ACCESS_KEY_ID')
```

## Configuration Files

### AWS Configuration

- **`aws/s3_config.json`** - S3 bucket configuration template
- **`aws/rds_config.json`** - RDS database configuration template
- **`aws/dynamodb_config.json`** - DynamoDB table configuration template
- **`aws/lambda_config.json`** - Lambda function configuration template
- **`aws/config.yaml`** - General AWS service configuration

### Alteryx Configuration

- **`alteryx/alteryx_config.json`** - Alteryx Designer Cloud connection settings

## What's Safe to Commit

✅ **Safe to commit:**
- Template files with placeholders (`*.json` in this directory)
- Configuration structure and schemas
- Default values and examples

❌ **NEVER commit:**
- Files with actual credentials
- `*.local.json` files (automatically ignored)
- AWS access keys or secret keys
- Database passwords
- API keys and tokens
- Personal email addresses (use examples)

## Checking for Exposed Credentials

Before committing, always check:

```bash
# Check what will be committed
git diff --cached

# Search for potential credentials
grep -r "AKIA" config/
grep -r "aws_secret" config/
grep -r "@gmail.com" config/
```

## Template Placeholders

When creating configuration templates, use these placeholder patterns:

- AWS Access Keys: `YOUR_AWS_ACCESS_KEY_ID`
- AWS Secret Keys: `YOUR_AWS_SECRET_ACCESS_KEY`
- Passwords: `YOUR_SECURE_PASSWORD` or `YOUR_RDS_PASSWORD`
- Endpoints: `your-resource-name.amazonaws.com`
- Bucket names: `your-bucket-name`
- Account IDs: `123456789012`
- Timestamps: `YYYY-MM-DDTHH:MM:SS.ssssss`

## Rotating Exposed Credentials

If you accidentally commit credentials:

1. **Immediately rotate the credentials in AWS:**
   - For IAM access keys: AWS Console → IAM → Users → Security Credentials → Make Inactive
   - Create new access keys
   - Update your local `.env` file

2. **Remove from git history:**
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   # Better: Use GitHub's secret scanning alerts
   ```

3. **Force push the cleaned history:**
   ```bash
   git push --force
   ```

4. **Update all team members** to pull the new history

## Best Practices

1. **Use AWS Secrets Manager** for production credentials
2. **Use IAM roles** instead of access keys when possible
3. **Enable AWS CloudTrail** to monitor credential usage
4. **Rotate credentials regularly** (every 90 days)
5. **Use least-privilege IAM policies**
6. **Never share credentials** via email, Slack, or other channels

## AWS Secrets Manager Example

For production, store credentials in AWS Secrets Manager:

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_creds = get_secret('prod/customer-analytics/rds')
db_password = db_creds['password']
```

## Support

For questions about configuration management:
- See [docs/troubleshooting.md](../docs/troubleshooting.md)
- Check [docs/deployment/deployment_guide.md](../docs/deployment/deployment_guide.md)
