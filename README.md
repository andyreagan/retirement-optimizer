# Retirement Planning Optimizer

A comprehensive retirement planning application with Monte Carlo simulation, Stripe payment integration, and multi-account optimization strategies.

## Features

### Core Functionality
- **Multi-Account Support**: 401k, Roth IRA, HSA, Brokerage accounts with proper tax treatment
- **Monte Carlo Simulation**: Range-based projections with market volatility modeling
- **Multiple Strategies**: Various contribution and withdrawal optimization strategies
- **Multi-Person Planning**: Joint projections with mortality calculations
- **Tax Optimization**: Sophisticated tax-aware contribution and withdrawal sequencing

### Payment & Subscription System
- **Stripe Integration**: Complete payment processing with webhooks
- **Flexible Pricing**: Individual pay-per-use packs and professional monthly subscriptions
- **Individual Packs**: $20 one-time purchase for personal retirement planning
- **Professional Plans**: $200/month unlimited subscriptions for advisors
- **Usage Tracking**: Monitor scenarios, Monte Carlo runs, and feature usage
- **Household Locking**: Individual packs lock to single household after first projection
- **Excel Export**: Paywall-protected spreadsheet export functionality

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
- **Subscription Management**: User dashboard with billing portal
- **Responsive Design**: Mobile-friendly interface

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+ (for building frontend)
- SQLite (included with Python)
- Stripe account (for payments)

> **Note**: If you encounter npm dependency conflicts, the frontend uses Vite 5.4.0 and Svelte 4.2.20 for compatibility.

### Quick Start (Single Server)

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - SECRET_KEY (generate new one for production)
   # - STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
   # - STRIPE_SECRET_KEY=sk_test_your_actual_secret_key
   # - STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Setup pricing tiers**
   ```bash
   python manage.py setup_new_pricing_tiers
   ```

8. **Build and serve the frontend**
   ```bash
   cd ..
   ./build_frontend.sh
   cd backend
   ```

9. **Start the server**
   ```bash
   python manage.py runserver
   ```

   🎉 **The entire application is now available at `http://localhost:8000`**

### Frontend Development

If you need to make frontend changes, you can use the build script:

```bash
./build_frontend.sh
```

This script will:
1. Build the frontend with Vite
2. Copy assets to Django's staticfiles directory
3. Notify you when complete

Django's auto-reload will pick up any backend changes automatically.

### Running Tests

#### Frontend Tests (Vitest + Svelte Testing Library)

The frontend uses Vitest for unit testing with Svelte Testing Library for component tests.

```bash
cd frontend

# Install test dependencies (if not already installed)
npm install

# Run tests once
npm run test:run

# Run tests in watch mode (for development)
npm test
```

**Available test suites:**
- `scenarioStore.test.js` - Tests for store logic, state management, and reactive updates
- `TabNavigation.test.js` - Tests for tab navigation component reactivity

**Example test output:**
```bash
✓ src/stores/scenarioStore.test.js (9 tests) 
✓ src/components/TabNavigation.test.js (partial - work in progress)
```

#### Backend Tests

```bash
# Run Django tests
cd backend
python manage.py test

# Run organized tests
python -m pytest ../tests/unit/        # Unit tests
python -m pytest ../tests/functional/  # Functional tests
python -m pytest ../tests/integration/ # Integration tests
```

### Testing the Application

1. **Access the application** at `http://localhost:8000`
2. **Create an account** and log in
3. **Set up a retirement scenario** with accounts and cash flows
4. **Run projections** and Monte Carlo simulations
5. **Test payment features** with Stripe test cards

## API Endpoints

### Core API
- `POST /api/projection/` - Run retirement projection
- `POST /api/monte-carlo/` - Run Monte Carlo simulation
- `GET /api/scenarios/` - Get saved scenarios
- `POST /api/export-excel/` - Export results to Excel

### Payment API
- `GET /api/payments/tiers/` - Get pricing tiers (packs and subscriptions)
- `POST /api/payments/create-checkout-session/` - Create Stripe checkout
- `POST /api/payments/purchase-pack/` - Purchase individual pack
- `POST /api/payments/track-usage/` - Track feature usage
- `GET /api/payments/payment-history/` - Get payment history

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

## Current Implementation Status

### ✅ **Completed Features**

#### Payment System
- **Stripe Integration**: Complete webhook handling, customer management
- **Dual Pricing Model**: Pay-per-use packs for individuals, monthly subscriptions for professionals
- **Individual Packs**: $20 for 25 projections, 5 scenarios, 10 Monte Carlo runs
- **Professional Monthly**: $200/month for unlimited usage and multi-client support
- **Household Locking**: Individual packs restrict to single household after first projection
- **Usage Tracking**: Real-time monitoring of feature usage and credits
- **Billing Portal**: Customer self-service billing management

#### Monte Carlo Simulation
- **Market Modeling**: Correlated stock/bond/inflation scenarios
- **Range Outputs**: Percentile bands (P10, P25, P50, P75, P90)
- **Parallel Processing**: Multi-threaded execution for performance
- **API Integration**: Full frontend integration

#### Core Functionality
- **Account Types**: 401k, Roth IRA, HSA, Brokerage with proper tax rules
- **Strategy Framework**: Multiple contribution/withdrawal strategies
- **Multi-Person Planning**: Joint projections with mortality modeling
- **Cash Flow Modeling**: Flexible income/expense patterns

### ⚠️ **Incomplete Implementations**

#### High Priority
1. **HSA Medical Expense Logic** (`backend/accounts/hsa.py:70`)
   - Currently assumes all withdrawals are medical
   - Need to track medical vs non-medical expenses separately

2. **Bucket Withdrawal Strategy** (`backend/strategies/withdrawal_strategies.py:185`)
   - Only placeholder implementation
   - Need proper time-horizon-based bucket logic

3. **Roth IRA Contribution Withdrawals** (`backend/accounts/roth_ira.py:70`)
   - Withdrawal logic has `pass` statement
   - Need to implement 5-year rule and contribution tracking

#### Medium Priority
1. **Abstract Base Class Methods** - Several base classes have `pass` statements
2. **Edge Case Handling** - Some strategies return `None` instead of proper errors
3. **Error Handling** - Could be more comprehensive in several areas

### 🔧 **Technical Debt**
- **Testing**: Limited test coverage
- **Documentation**: API documentation could be more comprehensive
- **Logging**: Could use more structured logging

## Development Notes

### Key Design Principles
- **Account Self-Management**: Each account type encapsulates its own rules (RMDs, penalties, limits)
- **Strategy Pattern**: Pluggable contribution/withdrawal strategies
- **Integrated Optimization**: Contribution and withdrawal strategies optimized together
- **Flexible Cash Flows**: No artificial "retirement age" - just cash flow patterns

### Adding New Features
1. **New Account Types**: Extend `BaseAccount` class
2. **New Strategies**: Implement contribution/withdrawal strategy interfaces
3. **New Endpoints**: Add to `api/views.py` and `api/urls.py`
4. **Frontend Components**: Add to `frontend/src/components/`

### Database Schema
- **Users**: Django's built-in user model
- **RetirementScenario**: Saved user scenarios
- **ProjectionResult**: Cached projection results
- **SubscriptionTier**: Pricing tiers with pack/subscription options
- **UserSubscription**: Subscription and usage tracking with credit system
- **PackPurchase**: Individual pack purchase records
- **UserHousehold**: Household data and locking for individual users
- **PaymentHistory**: Payment transaction records
- **UsageEvent**: Feature usage event tracking

### Security Considerations
- **API Authentication**: Session-based authentication
- **CORS**: Configured for development (localhost:5173)
- **Stripe Webhooks**: Signature verification enabled
- **Environment Variables**: Sensitive keys should be in environment variables

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Submit a pull request**

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- **Backend Issues**: Check Django logs at `backend/django.log`
- **Frontend Issues**: Check browser console and network tab
- **Payment Issues**: Verify Stripe webhook configuration
- **Database Issues**: Check SQLite database at `backend/db.sqlite3`