# Test Suite Documentation

## Overview

Comprehensive test suite for the Finance Analytics & Trading Co-Pilot API.

## Test Coverage

### API Tests (`test_api.py`)
- Market data endpoints
- Trading endpoints (signals, backtesting)
- Chat/AI endpoints
- GraphQL queries
- Authentication flows
- Health checks

### Authentication Tests (`test_auth.py`)
- Password hashing and verification
- JWT token creation and validation
- Role-based access control (RBAC)
- User authorization

### Backtesting Tests (`test_backtesting.py`)
- Backtest engine functionality
- Trade execution
- Position tracking
- Portfolio value calculations
- Performance metrics (Sharpe, Sortino, drawdown, etc.)

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_api.py
```

### Run tests with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run tests in parallel
```bash
pytest -n auto
```

### Run only fast tests
```bash
pytest -m "not slow"
```

## Test Database

Tests use an in-memory SQLite database that is created fresh for each test.
No test data persists between test runs.

## Fixtures

Common fixtures are defined in `conftest.py`:
- `test_db`: Fresh database session for each test
- `client`: Async HTTP client for API testing
- `sample_stock_data`: Sample market data
- `sample_news_data`: Sample news articles
- `sample_trading_signal`: Sample trading signals

## Writing New Tests

1. Create test file in `tests/` directory with `test_` prefix
2. Use pytest fixtures from `conftest.py`
3. Mark async tests with `@pytest.mark.asyncio`
4. Use descriptive test names that explain what is being tested
5. Include docstrings explaining the test purpose

Example:
```python
@pytest.mark.asyncio
async def test_feature_works_correctly(client):
    \"\"\"Test that feature X works as expected\"\"\"
    response = await client.get("/api/endpoint")
    assert response.status_code == 200
```

## Continuous Integration

Tests are run automatically on:
- Every commit
- Pull requests
- Before deployment

All tests must pass before code can be merged.
