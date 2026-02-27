# Project Current State

**Last updated:** 2026-02-27

## Overview

Retirement planning optimizer — Django backend + Svelte frontend SPA. Monte Carlo simulation, multi-account tax-optimized projections. Free to use, no payments.

## Branch / Git Status

- **Current branch:** `main`
- **Clean working tree** — no uncommitted changes
- **Recent history:**
  - `5b17abc` Remove all payment/subscription logic
  - `1d27b56` Add CURRENT_STATE.md and README inspiration links
  - `951afdc` Remove non-existent test data fixture loading
  - `13fca46` Update deprecated GitHub Actions to v4
  - `82645a9` Add PyJWT + cryptography deps

## Test Status (local, 2026-02-27)

| Suite | Status |
|-------|--------|
| Backend `manage.py test` | ✅ 2 passed |
| Backend `pytest tests/` | ✅ 27 passed (6 files) |
| Frontend `vitest` | ✅ 7 passed (2 files) |
| Functional (Playwright E2E) | ⚠️ Not run (requires server + Playwright browsers) |

## CI/CD

- GitHub Actions workflow at `.github/workflows/test.yml`
- Uses Postgres 15 service container (note: local dev uses SQLite)

## Architecture

```
backend/
  accounts/       # Account types: 401k, Roth IRA, HSA, Brokerage (OOP, self-contained rules)
  strategies/     # Contribution & withdrawal strategies (strategy pattern)
  api/            # Django REST views, serializers, auth, excel export, mortality, UsageEvent
    models.py     # RetirementScenario, ProjectionResult, UsageEvent, Person, CashFlowItem, etc.
    views.py      # run_projection, run_monte_carlo, get_scenarios, export_to_excel, etc.
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

functional_tests/ # 5 Playwright E2E test files (all skipped — need server + browsers)
```

## Known Incomplete Implementations

These are `pass` stubs / TODOs in the codebase:

1. **Roth IRA contribution withdrawals** (`accounts/roth_ira.py:81`) — no 5-year rule or contribution tracking
2. **HSA medical expense logic** (`accounts/hsa.py:82`) — assumes all withdrawals are medical
3. **Bucket withdrawal strategy** (`strategies/withdrawal_strategies.py:185`) — placeholder only
4. **Base class abstract methods** (`accounts/base.py`, `strategies/base.py`) — `pass` stubs (expected for ABCs)

## Key Decisions / Context

- **Single-server deploy:** Frontend built via `./build_frontend.sh`, served by Django's staticfiles
- **No payments / no limits:** All features freely available to authenticated users
- **Usage tracking:** `UsageEvent` model logs projection runs, monte carlo runs, scenario saves, excel exports — for analytics only, no limits enforced
- **No artificial "retirement age"** — uses cash flow patterns instead
- **Venv:** `.venv/` at project root (Python 3.11), must `source .venv/bin/activate` before backend commands
- **Google OAuth** configured via allauth (setup runs automatically on test/migrate)
- **Database:** SQLite locally (`backend/db.sqlite3`), Postgres 15 in CI

## Next Steps (suggested)

1. **Implement Roth IRA withdrawal logic** — highest-impact incomplete feature
2. **Implement HSA medical/non-medical expense tracking**
3. **Build out bucket withdrawal strategy**
4. **Expand test coverage** — especially for account withdrawal edge cases
5. **Deploy** — app has never been deployed anywhere yet
