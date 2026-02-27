# Project Current State

**Last updated:** 2026-02-27

## Overview

Retirement planning optimizer — Django backend + Svelte frontend SPA. Monte Carlo simulation, multi-account tax-optimized projections. Free to use, no payments.

## Branch / Git Status

- **Current branch:** `main`
- **Payments:** Removed — all Stripe/subscription/credit logic stripped out
- **Usage tracking:** Kept via `UsageEvent` model in `api` app (analytics only, no limits)

## Test Status (local, 2026-02-27)

| Suite | Status |
|-------|--------|
| Backend `manage.py test` | ✅ 2 passed |
| Backend `pytest tests/` | ✅ 27 passed |
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
  monte_carlo.py  # Monte Carlo simulation engine
  tests/          # 6 test files, 27 tests

frontend/
  src/
    components/   # 13 Svelte components (auth, scenarios, charts, etc.)
    stores/       # scenarioStore.js (main state), stores.js
  tests/          # 2 vitest files, 7 tests

functional_tests/ # 5 Playwright E2E test files
```

## Known Incomplete Implementations

1. **Roth IRA contribution withdrawals** (`accounts/roth_ira.py:70`) — no 5-year rule or contribution tracking
2. **HSA medical expense logic** (`accounts/hsa.py:70`) — assumes all withdrawals are medical
3. **Bucket withdrawal strategy** (`strategies/withdrawal_strategies.py:185`) — placeholder only
4. **Base class abstract methods** (`accounts/base.py`, `strategies/base.py`) — `pass` stubs (expected for ABCs)

## Key Decisions / Context

- **Single-server deploy:** Frontend built via `./build_frontend.sh`, served by Django's staticfiles
- **No payments / no limits:** All features freely available to authenticated users. Usage tracked for analytics only.
- **No artificial "retirement age"** — uses cash flow patterns instead
- **Venv:** `.venv/` at project root (Python 3.x), must `source .venv/bin/activate` before backend commands
- **Google OAuth** configured via allauth (setup runs automatically on test/migrate)

## Next Steps (suggested)

1. **Implement Roth IRA withdrawal logic** — highest-impact incomplete feature
2. **Implement HSA medical/non-medical expense tracking**
3. **Build out bucket withdrawal strategy**
4. **Expand test coverage** — especially for account withdrawal edge cases
