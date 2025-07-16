# Test Organization

This directory contains organized test files for the retirement optimization project.

## Directory Structure

- **functional/** - End-to-end functional tests
- **unit/** - Unit tests for individual components
- **integration/** - Integration tests for system interactions

## Running Tests

### Backend Tests
```bash
cd backend
python -m pytest ../tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Test Categories

### Functional Tests
- Complete user workflows
- Multi-component interactions
- Business logic validation

### Unit Tests
- Individual function/class testing
- API endpoint testing
- Algorithm validation

### Integration Tests
- Database interactions
- External service integrations
- Usage tracking systems