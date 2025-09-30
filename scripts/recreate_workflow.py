import pandas as pd
import numpy as np
from datetime import datetime

# Read data
transactions = pd.read_csv('data/sample/transactions.csv')
customers = pd.read_csv('data/sample/customers.csv')
products = pd.read_csv('data/sample/products.csv')

# Join data
df = transactions.merge(customers, on='customer_id', how='inner')
df = df.merge(products, on='product_id', how='inner')

# Calculate fields
df['actual_revenue'] = df['unit_price'] * df['quantity'] * (1 - df['discount_pct']/100)
df['days_since_transaction'] = (datetime.now() - pd.to_datetime(df['transaction_date'])).dt.days
df['customer_ltv'] = df['actual_revenue']  # Simplified without campaign data
df['churn_flag'] = (df['days_since_transaction'] > 90).astype(int)

# Save
df.to_csv('output/customer_360_python.csv', index=False)
print(f"Saved {len(df)} records")
