# Retirement Planning Optimizer

A comprehensive retirement planning application with Monte Carlo simulation and multi-account tax-optimized projections.

## Features

### Core Functionality

- **Multi-Account Support**: 401k, Roth IRA, HSA, Brokerage accounts with proper tax treatment
- **Monte Carlo Simulation**: Range-based projections with market volatility modeling
- **Multiple Strategies**: Various contribution and withdrawal optimization strategies
- **Multi-Person Planning**: Joint projections with mortality calculations
- **Tax Optimization**: Sophisticated tax-aware contribution and withdrawal sequencing
- **Excel Export**: Export projections to spreadsheet format

### Advanced Features

- **Mortality Modeling**: Joint survival probability calculations
- **Inflation Adjustments**: Real-time cash flow adjustments
- **Asset Allocation**: Dynamic portfolio rebalancing based on market scenarios
- **Risk Analysis**: Probability of success and shortfall analysis

## Architecture

### Backend (Django + Python)

- **Django REST API**: Full REST API with authentication
- **Account Classes**: OOP design with self-contained account logic
- **Strategy Pattern**: Pluggable contribution/withdrawal strategies
- **Monte Carlo Engine**: Parallel processing for performance

### Frontend (Svelte)

- **Svelte SPA**: Modern reactive UI
- **Chart.js Integration**: Interactive charts and visualizations
- **Responsive Design**: Mobile-friendly interface

## Local Development Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 16+ (for building frontend)
- SQLite (included with Python)

### Quick Start

1. **Clone and set up backend**

```bash
cd backend
uv sync
```

2. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your SECRET_KEY and Google OAuth credentials
```

3. **Run migrations and create superuser**

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

4. **Build frontend and start server**

```bash
cd ..
./build_frontend.sh
cd backend
uv run python manage.py runserver
```

🎉 **The application is available at `http://localhost:8000`**

### Running Tests

```bash
# Backend (Django)
cd backend
uv run python manage.py test

# Backend (pytest — full suite)
cd backend
uv run pytest tests/ -v

# Frontend (Vitest)
cd frontend
npm run test:run
```

## Docker Deployment

### Build and run locally

```bash
docker build -t retirement-optimizer .
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  -v retirement-data:/data \
  retirement-optimizer
```

### Using Docker Compose

```bash
# Copy .env.example to .env and fill in values
cp backend/.env.example .env

docker compose up -d
```

The compose file mounts a named volume at `/data` for the SQLite database. Set these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `ALLOWED_HOSTS` | No | Comma-separated hostnames (default: `localhost,127.0.0.1`) |
| `DATABASE_PATH` | No | SQLite path (default: `/data/db.sqlite3` in Docker) |
| `GOOGLE_OAUTH2_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_OAUTH2_CLIENT_SECRET` | No | Google OAuth client secret |
| `FRONTEND_URL` | No | Public URL for OAuth redirects |

### Synology NAS

1. Push the image to a registry (or build on the NAS):
   ```bash
   docker build -t your-registry/retirement-optimizer .
   docker push your-registry/retirement-optimizer
   ```
2. In Synology Container Manager, create a project using `docker-compose.yml`
3. Set environment variables in the Synology UI or via a `.env` file
4. Map a local folder to `/data` for persistent database storage

## API Endpoints

### Core API
- `POST /api/projection/` - Run retirement projection
- `POST /api/monte-carlo/` - Run Monte Carlo simulation
- `GET /api/scenarios/` - Get saved scenarios
- `DELETE /api/scenarios/<id>/` - Delete a scenario
- `GET /api/scenarios/<id>/results/` - Get scenario results
- `POST /api/export/excel/` - Export results to Excel
- `GET /api/scenarios/<id>/export/excel/` - Export saved scenario to Excel

### Authentication
- `GET /api/auth/csrf/` - Get CSRF token
- `GET /api/auth/user/` - Get current user
- `POST /api/auth/logout/` - Logout
- Google OAuth via `/accounts/google/login/`

## Key Design Principles

- **Account Self-Management**: Each account type encapsulates its own rules (RMDs, penalties, limits)
- **Strategy Pattern**: Pluggable contribution/withdrawal strategies
- **Flexible Cash Flows**: No artificial "retirement age" — just cash flow patterns
- **Usage Tracking**: All runs are tracked via `UsageEvent` for analytics (no limits enforced)

## Database Schema

- **Users**: Django's built-in user model
- **RetirementScenario**: Saved user scenarios with full request data
- **ProjectionResult**: Cached projection results
- **UsageEvent**: Feature usage event tracking (projection runs, monte carlo, exports)
- **Person / ScenarioPerson**: Multi-person scenario support
- **CashFlowItem**: Income/expense items with age ranges
- **AccountConfiguration**: Account settings per scenario

## Known Incomplete Implementations

1. **Roth IRA contribution withdrawals** — no 5-year rule or contribution tracking
2. **HSA medical expense logic** — assumes all withdrawals are medical
3. **Bucket withdrawal strategy** — placeholder only

## Inspiration

- https://www.ramseysolutions.com/
- https://moneyguy.com/guide/foo/
