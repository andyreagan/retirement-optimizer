#!/usr/bin/env python3
import requests
import json

# Test data for the API
test_data = {
    "name": "Test Scenario",
    "start_age": 35,
    "death_age": 85,
    "filing_status": "single",
    "annual_income": [100000] * 20 + [0] * 31,  # Work until 55, then retire
    "annual_expenses": [72000] * 20 + [48000] * 31,  # Lower expenses in retirement
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
        },
        {
            "account_type": "brokerage",
            "initial_balance": 10000,
            "parameters": {"initial_cost_basis": 8000}
        },
        {
            "account_type": "hsa",
            "initial_balance": 5000,
            "parameters": {}
        }
    ]
}

def test_api():
    try:
        response = requests.post(
            'http://localhost:8000/api/projection/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API Test Successful!")
            print(f"Final Balance: ${data['summary_stats']['final_balance']:,.0f}")
            print(f"Total Contributions: ${data['summary_stats']['total_contributions']:,.0f}")
            print(f"Total Withdrawals: ${data['summary_stats']['total_withdrawals']:,.0f}")
            print(f"Years Simulated: {data['summary_stats']['years_simulated']}")
        else:
            print("API Test Failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    test_api()