# Project Current State

**Last updated:** 2026-03-08

## Overview

Retirement planning optimizer — Django backend + Svelte frontend SPA. Monte Carlo simulation, multi-account tax-optimized projections. Free to use, no payments.

## Branch / Git Status

- **Current branch:** `main`

## Test Status (local, 2026-03-08)

| Suite | Status |
|-------|--------|
| Backend `pytest tests/` | ✅ 27 passed (6 files) |
| Backend `manage.py test` | ✅ 2 passed |
| Frontend `vitest` | ✅ 7 passed (2 files) |
| E2E `pytest functional_tests/` | ✅ 30 passed (Playwright + subprocess Django server) |

## Architecture

```
backend/
  accounts/       # Account types: 401k, Roth IRA, HSA, Brokerage (OOP, self-contained rules)
  strategies/     # Contribution & withdrawal strategies (strategy pattern)
  api/            # Django REST views, serializers, auth, excel export, mortality, UsageEvent
    models.py     # RetirementScenario, ProjectionResult, UsageEvent, Person, CashFlowItem, etc.
    views.py      # run_projection, run_monte_carlo, get_scenarios, export_to_excel, etc.
    test_auth_views.py  # Test-only login endpoint (DEBUG mode only)
  monte_carlo.py  # Monte Carlo simulation engine
  tests/          # 8 test files across unit/integration
    test_api_endpoints.py   # 5 tests — projection, monte carlo, save, auth
    test_models.py          # 5 tests — RetirementScenario, UsageEvent
    test_calculations.py    # 13 tests — tax, contributions, withdrawals, monte carlo helpers
    test_cashflow_integration.py  # 1 test
    test_strategy_integration.py  # 2 tests
    test_api_client.py      # 1 test

frontend/
  src/
    components/   # 14 Svelte components
      AuthManager.svelte, CashFlowManager.svelte, Charts.svelte,
      ExcelExport.svelte, LandingPage.svelte, MonteCarloConfig.svelte,
      MonteCarloResults.svelte, ParametersTab.svelte, PersonManager.svelte,
      Results.svelte, ScenarioHeader.svelte, ScenarioManager.svelte,
      StrategyManager.svelte, TabNavigation.svelte
    stores/       # scenarioStore.js (main state), stores.js (auth)
  tests/          # 2 vitest files, 7 tests
    TabNavigation.test.js, scenarioStore.test.js

functional_tests/       # Playwright E2E tests (30 tests)
  conftest.py           # Server management (subprocess), browser fixtures, auth helpers
  test_e2e_workflow.py  # 9 test classes covering the full user journey:
    TestLandingPage       (3 tests) — page loads, sign in visible, no app UI
    TestAuthentication    (3 tests) — login shows welcome, parameters tab, logout
    TestPeopleSetup       (3 tests) — load example couple, add/remove person
    TestCashFlowSetup     (3 tests) — load example items, add income/expense
    TestAccountSetup      (3 tests) — default accounts, add/remove account
    TestRunProjection     (4 tests) — run success, chart, summary, no-data graceful
    TestSaveAndLoad       (2 tests) — save named scenario, load from list
    TestMonteCarlo        (3 tests) — tab enabled/disabled, run simulation
    TestAPIDirectly       (6 tests) — projection, scenarios, user info, monte carlo APIs
```

## E2E Test Infrastructure

The E2E tests are fully self-contained:
- **`conftest.py`** starts a Django server on port 8765 as a subprocess (`--noreload`, `DEBUG=True`)
- Uses a **dedicated test SQLite database** (`test_e2e.sqlite3`) that's created/destroyed per session
- **`test-login` endpoint** (only available in DEBUG mode) enables authentication without Google OAuth
- Each test gets a **fresh browser context** (isolated cookies/state)
- The `authenticated_page` fixture handles CSRF token → test-login → page navigation

## Known Incomplete Implementations

1. **Roth IRA contribution withdrawals** (`accounts/roth_ira.py:81`) — no 5-year rule or contribution tracking
2. **HSA medical expense logic** (`accounts/hsa.py:82`) — assumes all withdrawals are medical
3. **Bucket withdrawal strategy** (`strategies/withdrawal_strategies.py:185`) — placeholder only
4. **Base class abstract methods** (`accounts/base.py`, `strategies/base.py`) — `pass` stubs (expected for ABCs)

## Key Decisions / Context

- **Single-server deploy:** Frontend built via `./build_frontend.sh`, served by Django's staticfiles
- **No payments / no limits:** All features freely available to authenticated users
- **Usage tracking:** `UsageEvent` model logs projection runs, monte carlo runs, scenario saves, excel exports — for analytics only, no limits enforced
- **No artificial "retirement age"** — uses cash flow patterns instead
- **uv:** Python dependencies managed via [uv](https://docs.astral.sh/uv/); run backend commands with `uv run` (e.g. `uv run python manage.py runserver`)
- **Google OAuth** configured via allauth (setup runs automatically on test/migrate)
- **Database:** SQLite locally (`backend/db.sqlite3`), Postgres 15 in CI

## Running Tests

```bash
# Everything
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# E2E only (builds frontend, starts server automatically)
make test-e2e
```

## Next Steps (suggested)

1. **Deploy** — app has never been deployed anywhere yet
2. **Implement Roth IRA withdrawal logic** — highest-impact incomplete feature
3. **Implement HSA medical/non-medical expense tracking**
4. **Build out bucket withdrawal strategy**
5. **Expand test coverage** — especially for account withdrawal edge cases
