# Project Current State

**Last updated:** 2026-02-27

## Overview

Retirement planning optimizer — Django backend + Svelte frontend SPA. Stripe payments, Monte Carlo simulation, multi-account tax-optimized projections.

## Branch / Git Status

- **Current branch:** `fix/comprehensive-test-fixes` (7 commits ahead of `main`)
- **Uncommitted:** Minor README.md tweak (added Inspiration links)
- **Main merges:** PRs #1 (scenario save/load) and #2 (failing tests) merged
- **Open branch work:** The current branch fixes CI — updated GH Actions to v4, added PyJWT + cryptography deps, removed non-existent fixture loading, cleaned up E2E artifact uploads. **Not yet merged to main.**

## Test Status (local, 2026-02-27)

| Suite | Status |
|-------|--------|
| Backend `manage.py test` | ✅ 16 passed, 2 skipped |
| Backend `pytest tests/` | ✅ 42 passed, 3 skipped |
| Frontend `vitest` | ✅ 10 passed (3 files) |
| Functional (Playwright E2E) | ⚠️ Not run (requires server + Playwright browsers) |

## CI/CD

- GitHub Actions workflow at `.github/workflows/test.yml`
- Uses Postgres 15 service container (note: local dev uses SQLite)
- CI runs unit tests → then E2E tests
- The `fix/comprehensive-test-fixes` branch fixes CI issues but hasn't been merged

## Architecture

```
backend/
  accounts/       # Account types: 401k, Roth IRA, HSA, Brokerage (OOP, self-contained rules)
  strategies/     # Contribution & withdrawal strategies (strategy pattern)
  api/            # Django REST views, serializers, auth, excel export, mortality
  payments/       # Stripe integration, subscriptions, packs, usage tracking
  monte_carlo.py  # Monte Carlo simulation engine
  tests/          # 8 test files, 42 tests

frontend/
  src/
    components/   # 16 Svelte components (auth, scenarios, charts, payments, etc.)
    stores/       # scenarioStore.js (main state), stores.js
  tests/          # 3 vitest files, 10 tests

functional_tests/ # 6 Playwright E2E test files
```

## Known Incomplete Implementations

These are `pass` stubs / TODOs in the codebase:

1. **Roth IRA contribution withdrawals** (`accounts/roth_ira.py:70`) — no 5-year rule or contribution tracking
2. **HSA medical expense logic** (`accounts/hsa.py:70`) — assumes all withdrawals are medical
3. **Bucket withdrawal strategy** (`strategies/withdrawal_strategies.py:185`) — placeholder only
4. **Base class abstract methods** (`accounts/base.py`, `strategies/base.py`) — `pass` stubs (expected for ABCs)

## Key Decisions / Context

- **Single-server deploy:** Frontend built via `./build_frontend.sh`, served by Django's staticfiles
- **Payment model:** $20 individual packs (25 projections) + $200/mo professional unlimited
- **No artificial "retirement age"** — uses cash flow patterns instead
- **Venv:** `.venv/` at project root (Python 3.x), must `source .venv/bin/activate` before backend commands
- **Google OAuth** configured via allauth (setup runs automatically on test/migrate)

## Next Steps (suggested)

1. **Merge `fix/comprehensive-test-fixes` to main** — CI fixes are ready
2. **Implement Roth IRA withdrawal logic** — highest-impact incomplete feature
3. **Implement HSA medical/non-medical expense tracking**
4. **Build out bucket withdrawal strategy**
5. **Expand test coverage** — especially for account withdrawal edge cases
6. **Commit the README.md tweak** or discard it
