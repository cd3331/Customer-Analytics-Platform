#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent.parent))
load_dotenv()

class SampleDataGenerator:
    def __init__(self):
        self.output_dir = Path("data/sample")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_customers = 100
        self.max_transactions = 500
        self.max_products = 20
        
        print("Sample Data Generator initialized")
        print(f"Output directory: {self.output_dir}")
    
    def generate_customers(self):
        print("\nGenerating customer data...")
        
        customers = []
        for i in range(1, self.max_customers + 1):
            customers.append({
                'customer_id': f'CUST{i:04d}',
                'email': f'customer{i}@example.com',
                'registration_date': (
                    datetime.now() - timedelta(days=random.randint(30, 365))
                ).isoformat(),
                'age_group': random.choice(['18-25', '26-35', '36-45', '46-55', '56+']),
                'region': random.choice(['North', 'South', 'East', 'West']),
                'tier': random.choice(['Bronze', 'Silver', 'Gold', 'Platinum'])
            })
        
        df = pd.DataFrame(customers)
        output_file = self.output_dir / "customers.csv"
        df.to_csv(output_file, index=False)
        
        print(f"Generated {len(df)} customers -> {output_file}")
        print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")
        
        return df

    def generate_transactions(self):
        print("\nGenerating transaction data...")
        
        transactions = []
        for i in range(self.max_transactions):
            transactions.append({
                'transaction_id': f'TRX{i:06d}',
                'customer_id': f'CUST{random.randint(1, self.max_customers):04d}',
                'product_id': f'PROD{random.randint(1, self.max_products):03d}',
                'transaction_date': (
                    datetime.now() - timedelta(days=random.randint(0, 180))
                ).isoformat(),
                'quantity': random.randint(1, 3),
                'unit_price': round(random.uniform(10, 200), 2),
                'discount_pct': random.choice([0, 5, 10, 15, 20]),
                'channel': random.choice(['online', 'store', 'mobile']),
                'payment_method': random.choice(['credit', 'debit', 'paypal', 'cash'])
            })
        
        df = pd.DataFrame(transactions)
        df['total_amount'] = df['unit_price'] * df['quantity'] * (1 - df['discount_pct']/100)
        
        output_file = self.output_dir / "transactions.csv"
        df.to_csv(output_file, index=False)
        
        print(f"Generated {len(df)} transactions -> {output_file}")
        print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")
        print(f"Total revenue: ${df['total_amount'].sum():,.2f}")
        
        return df

    def generate_products(self):
        print("\nGenerating product catalog...")
        
        categories = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports']
        products = []
        
        for i in range(1, self.max_products + 1):
            cost = round(random.uniform(5, 100), 2)
            price = round(cost * random.uniform(1.5, 3.0), 2)
            
            products.append({
                'product_id': f'PROD{i:03d}',
                'product_name': f'Product {i}',
                'category': categories[(i-1) % len(categories)],
                'subcategory': f'Subcat_{(i % 3) + 1}',
                'unit_cost': cost,
                'unit_price': price,
                'margin_pct': round(((price - cost) / price) * 100, 1),
                'supplier_id': f'SUPP{((i-1) % 5) + 1:02d}',
                'in_stock': random.choice([True, False]),
                'rating': round(random.uniform(3.0, 5.0), 1)
            })
        
        df = pd.DataFrame(products)
        output_file = self.output_dir / "products.csv"
        df.to_csv(output_file, index=False)
        
        print(f"Generated {len(df)} products -> {output_file}")
        print(f"Categories: {', '.join(df['category'].unique())}")
        
        return df

    def generate_all(self):
        print("\n" + "="*50)
        print("Starting Sample Data Generation")
        print("="*50)
        
        start_time = datetime.now()
        
        customers_df = self.generate_customers()
        transactions_df = self.generate_transactions()
        products_df = self.generate_products()
        
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "datasets": {
                "customers": len(customers_df),
                "transactions": len(transactions_df),
                "products": len(products_df)
            },
            "total_size_kb": sum(
                (self.output_dir / f).stat().st_size 
                for f in os.listdir(self.output_dir) 
                if f.endswith('.csv')
            ) / 1024,
            "generation_time_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        with open(self.output_dir / "generation_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "="*50)
        print("Sample Data Generation Complete!")
        print(f"Time taken: {summary['generation_time_seconds']:.2f} seconds")
        print(f"Total size: {summary['total_size_kb']:.2f} KB")
        print(f"Location: {self.output_dir.absolute()}")
        print("="*50)

def main():
    generator = SampleDataGenerator()
    generator.generate_all()

if __name__ == "__main__":
    main()
