# Alteryx Designer Cloud Workflow Setup

## Prerequisites
- Alteryx Designer Cloud trial account
- AWS credentials configured
- Data already in S3/RDS/DynamoDB

## Step-by-Step Workflow Creation

### 1. Log into Alteryx Designer Cloud
- URL: https://designercloud.alteryx.com
- Use your trial account credentials

### 2. Create New Workflow
- Click "Create New"
- Select "Workflow"
- Name: "Customer_360_Analytics"

### 3. Configure Data Connections

#### S3 Connection:
1. Click "Connections" → "Add Connection"
2. Select "Amazon S3"
3. Enter AWS credentials
4. Test connection

#### RDS Connection:
1. Add Connection → MySQL
2. Enter RDS endpoint from your .env
3. Database: marketing_db
4. Test connection

### 4. Build the Workflow

#### Step 1: Input Sales Data
- Drag "Input Data" tool
- Select S3 connection
- Browse to: data/sales/sales_data.csv
- Preview data

#### Step 2: Input Marketing Data
- Add second "Input Data" tool
- Select RDS connection
- Custom SQL Query

#### Step 3: Join Data
- Add "Join" tool
- Connect both inputs
- Join on: customer_id
- Type: Left Join

#### Step 4: Create Calculated Fields
- Add "Formula" tool
- Create new calculated fields for analysis

#### Step 5: Output Results
- Add "Output Data" tool
- Destination: S3
- Path: output/customer_analytics_results.csv

### 5. Run Workflow
- Click "Run Now"
- Monitor progress
- Check outputs in S3

## Expected Outputs
- customer_analytics_results.csv
- model_performance_metrics.json
- customer_segments.csv
