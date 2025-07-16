#!/usr/bin/env python3
import requests
import json

# Test data with the new cash flow items format
test_data = {
    "name": "New Cash Flow Test",
    "start_age": 35,
    "death_age": 85,
    "filing_status": "single",
    "cash_flow_items": [
        {
            "name": "Working Salary",
            "type": "income",
            "amount": 100000,
            "start_age": 35,
            "end_age": 54,
            "annual_adjustment": 0.03
        },
        {
            "name": "Social Security",
            "type": "income",
            "amount": 30000,
            "start_age": 67,
            "end_age": 85,
            "annual_adjustment": 0.02
        },
        {
            "name": "Working Expenses",
            "type": "expense",
            "amount": 72000,
            "start_age": 35,
            "end_age": 54,
            "annual_adjustment": 0.025
        },
        {
            "name": "Retirement Expenses",
            "type": "expense",
            "amount": 48000,
            "start_age": 55,
            "end_age": 85,
            "annual_adjustment": 0.025
        }
    ],
    "accounts": [
        {
            "account_type": "401k",
            "initial_balance": 50000,
            "parameters": {}
        },
        {
            "account_type": "roth_ira",
            "initial_balance": 20000,
            "parameters": {}
        }
    ]
}

def test_new_cashflow_api():
    try:
        response = requests.post(
            'http://localhost:8080/api/projection/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ New Cash Flow API Test Successful!")
            print(f"Final Balance: ${data['summary_stats']['final_balance']:,.0f}")
            print(f"Years Simulated: {data['summary_stats']['years_simulated']}")
            
            # Check first few years to verify cash flow calculation
            print("\nFirst 5 years:")
            for year_data in data['yearly_data'][:5]:
                print(f"  Age {year_data['age']}: Income=${year_data['income']:,.0f}, Expenses=${year_data['expenses']:,.0f}")
            
        else:
            print("❌ API Test Failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error making request: {e}")

if __name__ == "__main__":
    test_new_cashflow_api()