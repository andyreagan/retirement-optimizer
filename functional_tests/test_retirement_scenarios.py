"""
API-level functional tests for retirement scenarios (no browser needed).
"""
import pytest
import requests
import json


class TestProjectionAPI:
    """Hit the projection API directly to verify it works for anonymous users."""

    @pytest.mark.e2e
    def test_projection_api_anonymous(self, django_server):
        """Anonymous user can run a projection via the API."""
        url = f"{django_server}/api/projection/"
        payload = {
            "name": "API Test",
            "start_age": 30,
            "death_age": 90,
            "filing_status": "single",
            "annual_income": [80000] * 61,
            "annual_expenses": [50000] * 61,
            "accounts": [
                {
                    "account_type": "401k",
                    "initial_balance": 20000,
                    "parameters": {
                        "company_match_percentage": 0.5,
                        "company_match_limit": 0.06,
                    },
                }
            ],
            "contribution_strategy": "priority",
            "withdrawal_strategy": "tax_optimized",
        }

        # Need a CSRF token
        csrf_resp = requests.get(f"{django_server}/api/auth/csrf/")
        csrf_token = csrf_resp.json()["csrf_token"]
        cookies = csrf_resp.cookies

        resp = requests.post(
            url,
            json=payload,
            headers={"X-CSRFToken": csrf_token},
            cookies=cookies,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "yearly_data" in data
        assert "summary_stats" in data
        assert data["status"] == "success"
        assert len(data["yearly_data"]) == 61

    @pytest.mark.e2e
    def test_monte_carlo_api_anonymous(self, django_server):
        """Anonymous user can run Monte Carlo via the API."""
        url = f"{django_server}/api/monte-carlo/"
        payload = {
            "name": "MC Test",
            "start_age": 30,
            "death_age": 90,
            "filing_status": "single",
            "annual_income": [80000] * 61,
            "annual_expenses": [50000] * 61,
            "accounts": [
                {
                    "account_type": "401k",
                    "initial_balance": 20000,
                    "parameters": {
                        "company_match_percentage": 0.5,
                        "company_match_limit": 0.06,
                    },
                }
            ],
            "contribution_strategy": "priority",
            "withdrawal_strategy": "tax_optimized",
            "monte_carlo_config": {
                "num_simulations": 50,
                "stocks_mean_return": 0.07,
                "stocks_volatility": 0.15,
            },
        }

        csrf_resp = requests.get(f"{django_server}/api/auth/csrf/")
        csrf_token = csrf_resp.json()["csrf_token"]
        cookies = csrf_resp.cookies

        resp = requests.post(
            url,
            json=payload,
            headers={"X-CSRFToken": csrf_token},
            cookies=cookies,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "summary_stats" in data
        assert "percentiles" in data


class TestMultiPersonProjection:
    """Test multi-person scenario via API."""

    @pytest.mark.e2e
    def test_multi_person_projection(self, django_server):
        """Run a couple's retirement projection via API."""
        url = f"{django_server}/api/projection/"
        payload = {
            "name": "Couple Retirement Plan",
            "start_year": 2025,
            "filing_status": "married_filing_jointly",
            "people": [
                {"name": "Alex", "current_age": 35, "gender": "male"},
                {"name": "Sam", "current_age": 33, "gender": "female"},
            ],
            "cash_flow_items": [
                {
                    "name": "Alex Salary",
                    "type": "income",
                    "amount": 100000,
                    "start_age": 35,
                    "end_age": 65,
                    "annual_adjustment": 0.01,
                },
                {
                    "name": "Living Expenses",
                    "type": "expense",
                    "amount": 90000,
                    "start_age": 33,
                    "end_age": 120,
                    "annual_adjustment": 0.0,
                },
            ],
            "accounts": [
                {
                    "account_type": "401k",
                    "initial_balance": 150000,
                    "parameters": {},
                },
                {
                    "account_type": "brokerage",
                    "initial_balance": 50000,
                    "parameters": {"initial_cost_basis": 40000},
                },
            ],
        }

        csrf_resp = requests.get(f"{django_server}/api/auth/csrf/")
        csrf_token = csrf_resp.json()["csrf_token"]
        cookies = csrf_resp.cookies

        resp = requests.post(
            url,
            json=payload,
            headers={"X-CSRFToken": csrf_token},
            cookies=cookies,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["yearly_data"]) > 0

        first_year = data["yearly_data"][0]
        # Multi-person projections should have calendar year tracking
        assert "calendar_year" in first_year
