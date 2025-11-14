# API Reference

## Overview

The Customer Analytics Platform provides REST APIs via AWS Lambda and API Gateway for programmatic access to customer analytics data and metrics.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

Replace `{api-id}` and `{region}` with your deployed API Gateway values.

## Authentication

Currently, the API supports:
- **No Authentication** (development/demo mode)
- **API Key** (optional, configure in API Gateway)
- **IAM Authentication** (for AWS-to-AWS calls)

### Using API Keys (Optional)

If API keys are enabled:

```bash
curl -H "x-api-key: YOUR_API_KEY" https://your-api-url/metrics
```

## Endpoints

### 1. Health Check

Check if the API is running and healthy.

**Endpoint:** `GET /health`

**Parameters:** None

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is down

**Example:**
```bash
curl https://your-api-url/health
```

---

### 2. Get Customer Details

Retrieve detailed information about a specific customer including all behavioral sessions.

**Endpoint:** `GET /customer`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| customer_id | string | Yes | Unique customer identifier (e.g., "CUST0001") |

**Response:**
```json
{
  "customer_id": "CUST0001",
  "sessions": [
    {
      "timestamp": 1705315200,
      "event_type": "page_view",
      "session_id": "sess_12345",
      "page_url": "/products/electronics",
      "cart_value": 0,
      "converted": false
    },
    {
      "timestamp": 1705315260,
      "event_type": "cart_add",
      "session_id": "sess_12345",
      "page_url": "/cart",
      "cart_value": 299.99,
      "converted": false
    },
    {
      "timestamp": 1705315320,
      "event_type": "purchase",
      "session_id": "sess_12345",
      "page_url": "/checkout/success",
      "cart_value": 299.99,
      "converted": true
    }
  ],
  "total_sessions": 3
}
```

**Status Codes:**
- `200 OK`: Customer found
- `400 Bad Request`: Missing customer_id parameter
- `404 Not Found`: Customer not found
- `500 Internal Server Error`: Server error

**Example:**
```bash
curl "https://your-api-url/customer?customer_id=CUST0001"
```

**Python Example:**
```python
import requests

response = requests.get(
    "https://your-api-url/customer",
    params={"customer_id": "CUST0001"}
)
data = response.json()
print(f"Customer {data['customer_id']} has {data['total_sessions']} sessions")
```

---

### 3. Get Overall Metrics

Retrieve aggregated metrics across all customers.

**Endpoint:** `GET /metrics`

**Parameters:** None

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "total_sessions": 1247,
  "conversions": 189,
  "conversion_rate": 15.16,
  "total_revenue": 45678.90,
  "avg_cart_value": 241.68
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| timestamp | string | ISO 8601 timestamp of metric calculation |
| total_sessions | integer | Total number of customer sessions |
| conversions | integer | Number of sessions that resulted in purchase |
| conversion_rate | float | Percentage of sessions converting (0-100) |
| total_revenue | float | Sum of all purchase values |
| avg_cart_value | float | Average cart value for converted sessions |

**Status Codes:**
- `200 OK`: Metrics retrieved successfully
- `500 Internal Server Error`: Error calculating metrics

**Example:**
```bash
curl https://your-api-url/metrics
```

**Python Example:**
```python
import requests

response = requests.get("https://your-api-url/metrics")
metrics = response.json()

print(f"Conversion Rate: {metrics['conversion_rate']}%")
print(f"Total Revenue: ${metrics['total_revenue']:,.2f}")
print(f"Average Cart Value: ${metrics['avg_cart_value']:,.2f}")
```

---

### 4. Trigger Data Processing

Manually trigger the data processing Lambda function to aggregate and process customer data.

**Endpoint:** `POST /trigger-processing`

**Parameters:** None (optional body for future use)

**Request Body (Optional):**
```json
{
  "action": "aggregate"
}
```

**Response:**
```json
{
  "message": "Processing triggered",
  "requestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Status Codes:**
- `202 Accepted`: Processing job triggered successfully
- `500 Internal Server Error`: Failed to trigger processing

**Example:**
```bash
curl -X POST https://your-api-url/trigger-processing
```

**Python Example:**
```python
import requests

response = requests.post("https://your-api-url/trigger-processing")
result = response.json()
print(f"Processing started: {result['requestId']}")
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common Error Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 | Bad Request | Missing required parameters |
| 403 | Forbidden | Invalid API key or IAM permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Lambda function error, database error |
| 502 | Bad Gateway | API Gateway cannot reach Lambda |
| 504 | Gateway Timeout | Lambda function timeout (>30s) |

---

## Rate Limits

### Default Limits (No API Key)
- **Requests per second:** 10
- **Burst capacity:** 20

### With API Key
- **Requests per second:** 100
- **Burst capacity:** 200

### Free Tier Limits
- **Monthly requests:** 1,000,000 (Lambda Free Tier)
- **Monthly data transfer:** 1 GB out (API Gateway Free Tier)

---

## Code Examples

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_BASE_URL = 'https://your-api-url';

// Get metrics
async function getMetrics() {
  try {
    const response = await axios.get(`${API_BASE_URL}/metrics`);
    console.log('Metrics:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Get customer details
async function getCustomer(customerId) {
  try {
    const response = await axios.get(`${API_BASE_URL}/customer`, {
      params: { customer_id: customerId }
    });
    console.log('Customer:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

getMetrics();
getCustomer('CUST0001');
```

### Python

```python
import requests
from typing import Dict, Any

API_BASE_URL = 'https://your-api-url'

class CustomerAnalyticsAPI:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers['x-api-key'] = api_key

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details"""
        response = requests.get(
            f"{self.base_url}/customer",
            params={"customer_id": customer_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_metrics(self) -> Dict[str, Any]:
        """Get overall metrics"""
        response = requests.get(f"{self.base_url}/metrics", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def trigger_processing(self) -> Dict[str, Any]:
        """Trigger data processing"""
        response = requests.post(
            f"{self.base_url}/trigger-processing",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
api = CustomerAnalyticsAPI(API_BASE_URL)

# Check health
health = api.health_check()
print(f"API Status: {health['status']}")

# Get metrics
metrics = api.get_metrics()
print(f"Conversion Rate: {metrics['conversion_rate']}%")

# Get customer
customer = api.get_customer('CUST0001')
print(f"Customer has {customer['total_sessions']} sessions")
```

### cURL

```bash
#!/bin/bash

API_URL="https://your-api-url"

# Health check
echo "=== Health Check ==="
curl "$API_URL/health"
echo

# Get metrics
echo "=== Overall Metrics ==="
curl "$API_URL/metrics" | jq
echo

# Get customer
echo "=== Customer Details ==="
curl "$API_URL/customer?customer_id=CUST0001" | jq
echo

# Trigger processing
echo "=== Trigger Processing ==="
curl -X POST "$API_URL/trigger-processing" | jq
echo
```

---

## Data Models

### Customer Session Object

```typescript
interface CustomerSession {
  timestamp: number;        // Unix timestamp
  event_type: string;       // "page_view" | "cart_add" | "purchase"
  session_id: string;       // Session identifier
  page_url: string;         // Page URL visited
  cart_value: number;       // Current cart value in dollars
  converted: boolean;       // Whether session resulted in purchase
}
```

### Metrics Object

```typescript
interface Metrics {
  timestamp: string;        // ISO 8601 timestamp
  total_sessions: number;   // Total session count
  conversions: number;      // Number of conversions
  conversion_rate: number;  // Percentage (0-100)
  total_revenue: number;    // Total revenue in dollars
  avg_cart_value: number;   // Average cart value in dollars
}
```

---

## Testing the API

### Using Postman

1. **Import collection:**
   - Create new collection: "Customer Analytics API"
   - Set base URL as collection variable

2. **Add requests:**
   - GET Health Check: `{{baseUrl}}/health`
   - GET Metrics: `{{baseUrl}}/metrics`
   - GET Customer: `{{baseUrl}}/customer?customer_id=CUST0001`
   - POST Trigger: `{{baseUrl}}/trigger-processing`

3. **Create test scripts:**
   ```javascript
   pm.test("Status code is 200", function () {
       pm.response.to.have.status(200);
   });

   pm.test("Response has required fields", function () {
       var jsonData = pm.response.json();
       pm.expect(jsonData).to.have.property('timestamp');
   });
   ```

### Using Python Script

```python
# scripts/test_api.py
import requests
import sys

def test_api(base_url):
    """Test all API endpoints"""

    print("Testing API at:", base_url)

    # Test health check
    print("\n1. Testing /health...")
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
    print("✓ Health check passed")

    # Test metrics
    print("\n2. Testing /metrics...")
    response = requests.get(f"{base_url}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert 'conversion_rate' in data
    print(f"✓ Metrics returned: {data['conversion_rate']}% conversion rate")

    # Test customer endpoint
    print("\n3. Testing /customer...")
    response = requests.get(f"{base_url}/customer", params={"customer_id": "CUST0001"})
    assert response.status_code in [200, 404]
    print("✓ Customer endpoint working")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <api_url>")
        sys.exit(1)

    test_api(sys.argv[1])
```

---

## Deployment

### Getting Your API URL

After deploying Lambda functions:

```bash
# Get API Gateway URL
aws apigatewayv2 get-apis --query 'Items[?Name==`customer-analytics-api`].ApiEndpoint' --output text
```

Or check in AWS Console:
1. Go to API Gateway
2. Find "customer-analytics-api"
3. Copy the "Invoke URL"

### Environment Variables

Lambda functions require these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| DYNAMODB_TABLE | DynamoDB table name | customer-behavior-events |
| S3_BUCKET | S3 bucket for data | customer-analytics-20240115 |
| REGION | AWS region | us-east-1 |

---

## Monitoring

### CloudWatch Metrics

Monitor API performance:

```bash
# Get API invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=customer-analytics-api \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 3600 \
  --statistics Sum

# Get API error count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=customer-analytics-api \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### Logs

View Lambda logs:

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/customer-analytics-api --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/customer-analytics-api \
  --filter-pattern "ERROR"
```

---

## Support

For API issues or questions:
- GitHub Issues: https://github.com/your-username/customer-analytics-platform/issues
- Email: cd3331github@gmail.com
- Troubleshooting Guide: [docs/troubleshooting.md](troubleshooting.md)
