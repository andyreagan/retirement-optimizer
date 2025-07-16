#!/usr/bin/env python3
import requests
import json

# Test data for multi-person scenario
test_data = {
    "name": "Couple Retirement Plan",
    "start_year": 2025,
    "filing_status": "married_filing_jointly",
    "people": [
        {
            "name": "Alex",
            "current_age": 35,
            "gender": "male"
        },
        {
            "name": "Sam", 
            "current_age": 33,
            "gender": "female"
        }
    ],
    "cash_flow_items": [
        {
            "name": "Alex Salary",
            "type": "income",
            "amount": 100000,
            "start_age": 35,
            "end_age": 65,
            "annual_adjustment": 0.01
        },
        {
            "name": "Sam Salary",
            "type": "income", 
            "amount": 80000,
            "start_age": 33,
            "end_age": 63,
            "annual_adjustment": 0.015
        },
        {
            "name": "Social Security Alex",
            "type": "income",
            "amount": 35000,
            "start_age": 67,
            "end_age": 120,
            "annual_adjustment": 0.0
        },
        {
            "name": "Social Security Sam",
            "type": "income",
            "amount": 30000,
            "start_age": 67,
            "end_age": 120,
            "annual_adjustment": 0.0
        },
        {
            "name": "Living Expenses",
            "type": "expense",
            "amount": 90000,
            "start_age": 33,
            "end_age": 120,
            "annual_adjustment": 0.0
        },
        {
            "name": "Healthcare Premium",
            "type": "expense",
            "amount": 15000,
            "start_age": 65,
            "end_age": 120,
            "annual_adjustment": 0.02
        }
    ],
    "accounts": [
        {
            "account_type": "401k",
            "initial_balance": 150000,
            "parameters": {}
        },
        {
            "account_type": "roth_ira",
            "initial_balance": 75000,
            "parameters": {}
        },
        {
            "account_type": "brokerage",
            "initial_balance": 50000,
            "parameters": {"initial_cost_basis": 40000}
        }
    ]
}

def test_multi_person_api():
    try:
        response = requests.post(
            'http://localhost:8080/api/projection/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Multi-Person API Test Successful!")
            
            # Check if new columns exist
            yearly_data = data['yearly_data']
            first_year = yearly_data[0]
            
            print(f"Final Balance: ${data['summary_stats']['final_balance']:,.0f}")
            print(f"Years Simulated: {data['summary_stats']['years_simulated']}")
            
            # Check for new multi-person columns
            if 'calendar_year' in first_year:
                print(f"✅ Calendar year tracking: {first_year['calendar_year']}")
            if 'survival_prob_both' in first_year:
                print(f"✅ Joint survival probability: {first_year['survival_prob_both']:.3f}")
            if 'net_worth_95pct_mortality' in first_year:
                print(f"✅ Net worth at 95% mortality: ${first_year['net_worth_95pct_mortality']:,.0f}")
            
            print("\nFirst 5 years of projection:")
            for year_data in yearly_data[:5]:
                age_info = f"Ages {year_data.get('youngest_age', '?')}-{year_data.get('oldest_age', '?')}"
                survival = f"{year_data.get('survival_prob_both', 0):.3f}" if 'survival_prob_both' in year_data else "N/A"
                print(f"  {year_data.get('calendar_year', '?')} ({age_info}): "
                      f"Income=${year_data['income']:,.0f}, "
                      f"Expenses=${year_data['expenses']:,.0f}, "
                      f"Both Alive Prob={survival}")
            
        else:
            print("❌ API Test Failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error making request: {e}")

if __name__ == "__main__":
    test_multi_person_api()