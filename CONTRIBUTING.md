# Contributing to StockLighthouse

Thank you for your interest in contributing to StockLighthouse! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Templates](#issue-templates)
- [Branch Naming](#branch-naming)
- [Commit Messages](#commit-messages)
- [Documentation](#documentation)
- [Agent Tasks](#agent-tasks)

## Code of Conduct

- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on what is best for the community and project
- Show empathy towards other community members

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/StockLighthouse.git
cd StockLighthouse
```

### 2. Set Up Development Environment

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# Or for bug fixes:
git checkout -b fix/bug-description
```

### 4. Make Your Changes

- Write clean, maintainable code
- Follow coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 5. Test Your Changes

**Backend:**
```bash
cd backend
PYTHONPATH=src pytest tests/ -v --cov=stocklighthouse
```

**Frontend:**
```bash
cd frontend
npm test
npm run lint
npm run e2e  # If applicable
```

### 6. Commit and Push

```bash
git add .
git commit -m "feat: Add new feature"
git push origin feature/your-feature-name
```

### 7. Open a Pull Request

- Go to GitHub and create a Pull Request
- Fill out the PR template completely
- Link related issues
- Request reviews

## Development Workflow

### Standard Workflow

1. **Issue First**: Create or claim an issue before starting work
2. **Branch**: Create a feature or fix branch from `main`
3. **Develop**: Make changes following coding standards
4. **Test**: Write and run tests locally
5. **Document**: Update relevant documentation
6. **Commit**: Make atomic commits with clear messages
7. **PR**: Open a pull request with complete description
8. **Review**: Address review feedback
9. **Merge**: Maintainers will merge after approval

### For Maintainers

- Review PRs within 48 hours
- Run CI/CD pipelines before merging
- Ensure tests pass and coverage is maintained
- Squash commits if necessary
- Update changelog

## Coding Standards

### Python (Backend)

#### Style Guide

Follow **PEP 8** Python style guide:

```python
# Good: Clear naming, proper spacing
def calculate_weighted_average(values: list[float], weights: list[float]) -> float:
    """
    Calculate weighted average of values.
    
    Args:
        values: List of numeric values
        weights: List of weights corresponding to values
        
    Returns:
        Weighted average as float
    """
    if not values or len(values) != len(weights):
        raise ValueError("Values and weights must have same length")
    
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight
```

#### Key Python Standards

- **Type Hints**: Always use type hints for function signatures
```python
def fetch_stock(symbol: str, use_cache: bool = True) -> TickerData:
    pass
```

- **Docstrings**: Use Google-style docstrings for all public functions
```python
def normalize(symbol: str, raw_data: Dict[str, Any]) -> StockKPIs:
    """
    Normalize raw provider data into standardized StockKPIs.
    
    Args:
        symbol: Stock ticker symbol
        raw_data: Raw data dictionary from provider
        
    Returns:
        Normalized StockKPIs object
        
    Raises:
        ValueError: If symbol is empty
    """
```

- **Imports**: Order imports (standard library, third-party, local)
```python
# Standard library
import json
from typing import Dict, Any

# Third-party
import yfinance as yf
from pydantic import BaseModel

# Local
from stocklighthouse.models import StockKPIs
```

- **Error Handling**: Use specific exceptions
```python
# Good
try:
    result = risky_operation()
except KeyError as e:
    logger.error(f"Missing key: {e}")
    raise ValueError(f"Required field not found: {e}")

# Bad
try:
    result = risky_operation()
except Exception:
    pass  # Silent failure
```

- **Constants**: Use UPPER_CASE for constants
```python
CACHE_TTL_SECONDS = 300
MAX_RETRIES = 3
DEFAULT_BACKOFF = 1.0
```

### TypeScript/JavaScript (Frontend)

#### Style Guide

Follow **ESLint** configuration in the project:

```typescript
// Good: Typed, clear, functional
interface StockKPIs {
  symbol: string;
  price: number | null;
  sector: string | null;
}

const formatPrice = (price: number | null): string => {
  if (price === null) return 'N/A';
  return `$${price.toFixed(2)}`;
};

// Component with proper typing
const StockCard: React.FC<{ stock: StockKPIs }> = ({ stock }) => {
  return (
    <div className="stock-card">
      <h3>{stock.symbol}</h3>
      <p>{formatPrice(stock.price)}</p>
    </div>
  );
};
```

#### Key TypeScript Standards

- **Strict Mode**: Enable strict TypeScript checking
- **Interfaces**: Define interfaces for all data structures
- **Type Safety**: Avoid `any` type, use `unknown` if needed
- **Functional Components**: Use functional components with hooks
- **Props Typing**: Always type component props
```typescript
interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, placeholder = 'Search...' }) => {
  // Component implementation
};
```

### CSS Standards

- **Modular CSS**: Use CSS modules for component styles
- **Naming**: Use kebab-case for class names
- **Responsive**: Mobile-first responsive design
- **Variables**: Use CSS custom properties for theming

```css
/* Good: Modular, reusable */
.stock-card {
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: var(--bg-primary);
}

.stock-card__title {
  font-size: var(--font-lg);
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .stock-card {
    padding: var(--spacing-sm);
  }
}
```

## Testing Requirements

### Test Coverage

- Maintain **90%+ code coverage** for all new code
- All new features must include tests
- Bug fixes must include regression tests

### Backend Testing

```bash
cd backend

# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run with coverage
PYTHONPATH=src pytest tests/ --cov=stocklighthouse --cov-report=html

# View coverage report
open htmlcov/index.html
```

#### Test Structure

```python
# tests/test_feature.py
import pytest
from stocklighthouse.feature import function_to_test

class TestFeature:
    """Test suite for feature module."""
    
    def test_basic_functionality(self):
        """Test basic use case."""
        result = function_to_test("input")
        assert result == "expected"
    
    def test_edge_case_empty_input(self):
        """Test with empty input."""
        result = function_to_test("")
        assert result is None
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(None)
```

### Frontend Testing

```bash
cd frontend

# Unit tests
npm test

# E2E tests (requires running backend and frontend)
npm run e2e

# Lint
npm run lint
```

#### Component Test Example

```typescript
// src/components/__tests__/SearchBar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchBar } from '../SearchBar';

describe('SearchBar', () => {
  it('renders with placeholder', () => {
    render(<SearchBar onSearch={jest.fn()} />);
    expect(screen.getByPlaceholderText('Search stocks...')).toBeInTheDocument();
  });
  
  it('calls onSearch when user types', () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'AAPL' } });
    
    expect(onSearch).toHaveBeenCalledWith('AAPL');
  });
});
```

## Pull Request Process

### PR Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (linters pass)
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Coverage maintained at 90%+
- [ ] Documentation updated (README, docstrings, comments)
- [ ] No console errors or warnings
- [ ] Commits are clean and well-described
- [ ] PR description is complete
- [ ] Related issues are linked

### PR Template

When opening a PR, include:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123
Relates to #456

## Testing
- [ ] Unit tests added/updated
- [ ] E2E tests added/updated (if UI change)
- [ ] Manual testing completed

## How to Test Locally
1. Step-by-step instructions
2. To test the changes
3. In your local environment

## Screenshots (if applicable)
Attach screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No new warnings
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: At least one maintainer review required
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves PR
5. **Merge**: Maintainer merges using squash or rebase

### Screenshots for UI Changes

For any UI changes, include screenshots in `.test-results/screenshots/<issue-number>/`:

```bash
# E2E tests automatically capture screenshots
npm run e2e

# Screenshots saved to:
.test-results/screenshots/<issue-number>/
  ├── before.png
  ├── after.png
  └── feature-demo.png
```

## Issue Templates

### Bug Report

```markdown
**Describe the bug**
Clear description of what the bug is

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment:**
- OS: [e.g., macOS, Windows, Linux]
- Browser: [e.g., Chrome, Firefox]
- Version: [e.g., 1.0.0]
```

### Feature Request

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of what you want to happen

**Describe alternatives you've considered**
Any alternative solutions considered

**Additional context**
Any other context or screenshots
```

### Agent Task Template

Use the "Agent Task" issue template for work assigned to agents:

```markdown
**Agent**: [agent-name]
**Manifest ID**: [agent-manifest-id]

**Task Description**
Clear description of the task

**Acceptance Criteria**
- [ ] Criterion 1
- [ ] Criterion 2

**Technical Details**
Any technical requirements or constraints
```

## Branch Naming

Use the following branch naming conventions:

### Standard Branches
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/documentation-update` - Documentation only
- `refactor/code-improvement` - Code refactoring
- `test/test-addition` - Adding tests
- `chore/maintenance-task` - Maintenance tasks

### Agent Branches
- `agent/<agent-name>/<short-description>` - Agent-assigned tasks

### Examples
```bash
# Good branch names
feature/sector-analysis
fix/price-calculation-error
docs/api-documentation
refactor/ingestor-caching
test/normalizer-edge-cases
agent/docs-agent/update-readme

# Bad branch names
my-changes
fix
update
branch1
```

## Commit Messages

### Format

Follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring without behavior change
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```bash
# Good commit messages
feat(ingestor): Add support for batch fetching with retry logic
fix(normalizer): Handle NaN values in P/E ratio calculation
docs(readme): Update installation instructions for Python 3.10+
test(analyzer): Add edge case tests for empty sector aggregation

# Bad commit messages
fixed bug
updates
working on feature
asdf
```

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues in footer ("Fixes #123")
- Explain "what" and "why", not "how"

## Documentation

### Code Documentation

#### Python Docstrings

Use Google-style docstrings:

```python
def calculate_metric(data: list[float], threshold: float = 0.5) -> float:
    """
    Calculate a specific metric from data.
    
    This function processes the input data and applies a threshold
    to compute a final metric value.
    
    Args:
        data: List of floating point values to process
        threshold: Minimum threshold value (default: 0.5)
        
    Returns:
        Calculated metric as a float value
        
    Raises:
        ValueError: If data is empty or threshold is negative
        
    Example:
        >>> calculate_metric([1.0, 2.0, 3.0])
        2.0
        >>> calculate_metric([1.0, 2.0], threshold=1.5)
        1.5
    """
```

#### Inline Comments

- Explain "why", not "what"
- Keep comments up to date with code
- Use comments for complex logic only

```python
# Good: Explains why
# Use exponential backoff to handle rate limiting
backoff = initial_backoff * (multiplier ** attempt)

# Bad: States the obvious
# Set x to 5
x = 5
```

### README Updates

When adding features:
1. Update main README.md with usage examples
2. Update component-specific READMEs
3. Add to Table of Contents if needed
4. Include code examples
5. Update troubleshooting section if applicable

## Agent Tasks

For work assigned to specialized agents:

### Requirements

- Use the "Agent Task" issue template
- Branch naming: `agent/<agent-name>/<short-description>`
- Include agent manifest ID in PR description
- Specify which agent handled the task

### PR Requirements for Agent Tasks

- [ ] Tests (pytest for backend, Playwright for UI)
- [ ] "How to run locally" section in PR body
- [ ] Screenshots for UI changes in `.test-results/screenshots/<issue-number>/`

### Labels

Apply appropriate labels:
- `agent-task` - Task assigned to an agent
- `qa-needed` - Requires QA review
- `review-request` - Ready for review
- `backend` / `frontend` - Component affected
- `documentation` - Documentation update

## Questions?

- Check existing documentation first
- Search existing issues and discussions
- Open a discussion for general questions
- Open an issue for bugs or feature requests
- Tag maintainers for urgent matters

## Thank You!

Thank you for contributing to StockLighthouse! Your contributions help make this project better for everyone. 🙏