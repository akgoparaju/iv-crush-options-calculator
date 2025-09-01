# Contributing to Advanced Options Trading Calculator

Thank you for your interest in contributing to the Advanced Options Trading Calculator! This document provides guidelines for contributing to this educational options analysis system.

## 🎯 Project Mission

This project is designed to provide **educational and research tools** for options trading analysis. All contributions should align with our core mission of creating high-quality, educational content that helps users understand options trading concepts and risk management.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Types](#contribution-types)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation Standards](#documentation-standards)
- [Issue Reporting](#issue-reporting)

## 📜 Code of Conduct

### Our Standards

- **Educational Focus**: All contributions should enhance the educational value of the project
- **Professional Tone**: Maintain professional, respectful communication
- **Risk Awareness**: Always emphasize educational purpose and risk disclaimers
- **Quality First**: Prioritize code quality, testing, and documentation
- **Inclusive Environment**: Welcome contributors of all backgrounds and experience levels

### Expected Behavior

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community and educational mission
- Show empathy toward other community members

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.9+** (Python 3.13+ recommended)
- **Git** for version control
- **Basic understanding** of options trading concepts
- **Familiarity** with Python development practices

### Areas for Contribution

We welcome contributions in the following areas:

- **🐛 Bug fixes**: Resolve issues and improve reliability
- **✨ Feature enhancements**: Add new analysis capabilities
- **📚 Documentation**: Improve guides, examples, and API documentation
- **🧪 Testing**: Expand test coverage and edge case validation
- **🎨 User Interface**: Improve CLI output formatting and usability
- **📊 Strategy Research**: Add new educational trading strategies
- **⚡ Performance**: Optimize analysis speed and resource usage

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/iv-crush-options-calculator.git
cd iv-crush-options-calculator
```

### 2. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt  # Optional
```

### 3. Verify Installation

```bash
# Run tests to ensure everything works
python3 test_modular.py

# Test demo functionality
python3 main.py --demo --earnings --symbol AAPL

# Check version
python3 main.py --version
```

### 4. Create Feature Branch

```bash
# Create a descriptive branch name
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

## 🎨 Code Style Guidelines

### Python Code Standards

- **PEP 8 Compliance**: Follow Python PEP 8 style guidelines
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Include comprehensive docstrings for all functions and classes
- **Error Handling**: Implement robust error handling with meaningful messages
- **Logging**: Use appropriate logging levels for debugging and monitoring

### Code Organization

```python
# Good: Clear function with type hints and docstring
def calculate_calendar_spread(
    symbol: str, 
    front_expiration: str, 
    back_expiration: str,
    strike: float
) -> Dict[str, Any]:
    """
    Calculate calendar spread metrics for given parameters.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        front_expiration: Front month expiration date
        back_expiration: Back month expiration date  
        strike: Strike price for the calendar spread
        
    Returns:
        Dictionary containing spread analysis results
        
    Raises:
        ValueError: If invalid parameters provided
    """
    # Implementation here
    pass
```

### Naming Conventions

- **Variables**: `snake_case` (e.g., `iv_crush_severity`)
- **Functions**: `snake_case` (e.g., `analyze_calendar_spread`)
- **Classes**: `PascalCase` (e.g., `OptionsAnalyzer`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_RISK_FREE_RATE`)
- **Files/Modules**: `snake_case` (e.g., `trade_construction.py`)

### Educational Code Requirements

- **Risk Disclaimers**: Include appropriate educational disclaimers
- **Clear Variable Names**: Use descriptive names that explain trading concepts
- **Educational Comments**: Explain complex trading logic for learning purposes
- **Validation**: Validate all financial calculations and assumptions

## 🧪 Testing Requirements

### Test Coverage Standards

- **Unit Tests**: Minimum 80% code coverage for new features
- **Integration Tests**: Test module interactions and data flow
- **Edge Cases**: Test boundary conditions and error scenarios
- **Demo Mode**: Ensure all features work in demo/educational mode

### Running Tests

```bash
# Run the main test suite
python3 test_modular.py

# Run specific test modules (if applicable)
python3 -m pytest tests/ -v

# Test with demo data
python3 main.py --demo --earnings --trade-construction --symbol AAPL
```

### Test Guidelines

- **Test Names**: Use descriptive names explaining what's being tested
- **Demo Data**: Use realistic but clearly fake data for testing
- **Error Testing**: Test error conditions and edge cases
- **Performance**: Include tests for performance-critical functions

### Example Test Structure

```python
def test_calendar_spread_calculation():
    """Test calendar spread calculation with valid inputs."""
    # Arrange
    test_data = create_demo_options_data()
    
    # Act
    result = analyze_calendar_spread(test_data)
    
    # Assert
    assert result['net_debit'] > 0
    assert result['max_profit'] > result['net_debit']
    assert 'educational_disclaimer' in result
```

## 📋 Pull Request Process

### Before Submitting

1. **✅ Code Quality**
   - [ ] Code follows style guidelines
   - [ ] All functions have docstrings
   - [ ] Type hints are included
   - [ ] No lint warnings or errors

2. **✅ Testing**
   - [ ] All existing tests pass
   - [ ] New tests added for new features
   - [ ] Demo mode functionality verified
   - [ ] Edge cases considered

3. **✅ Documentation**
   - [ ] README.md updated if needed
   - [ ] Code comments explain complex logic
   - [ ] Educational disclaimers included
   - [ ] Strategy documentation updated

### Pull Request Template

When submitting a pull request, please include:

```markdown
## 📋 Description
Brief description of changes and motivation.

## 🎯 Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## ✅ Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Demo mode tested
- [ ] Edge cases considered

## 📚 Educational Impact
- [ ] Enhances educational value
- [ ] Includes appropriate disclaimers
- [ ] Clear explanations for learning

## 📖 Documentation
- [ ] Code is well-documented
- [ ] README.md updated (if applicable)
- [ ] Strategy guide updated (if applicable)
```

### Review Process

1. **Automated Checks**: Code will be automatically checked for style and tests
2. **Educational Review**: Ensure educational value and appropriate disclaimers
3. **Technical Review**: Code quality, performance, and integration
4. **Testing Review**: Verify test coverage and demo functionality
5. **Documentation Review**: Check for clarity and completeness

## 📚 Documentation Standards

### Code Documentation

- **Docstrings**: Use Google-style docstrings for all public functions
- **Type Hints**: Include comprehensive type annotations
- **Educational Comments**: Explain trading concepts and financial logic
- **Examples**: Provide usage examples in docstrings

### User Documentation

- **Clear Instructions**: Step-by-step guides for new features
- **Educational Context**: Explain the trading concepts behind features
- **Risk Warnings**: Include appropriate disclaimers and warnings
- **Examples**: Real-world usage examples with demo data

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Clear title**: Descriptive summary of the issue
- **Steps to reproduce**: Exact steps to trigger the bug
- **Expected behavior**: What should have happened
- **Actual behavior**: What actually happened
- **Environment**: Python version, OS, dependencies
- **Demo mode**: Whether the issue occurs in demo mode
- **Log files**: Relevant error messages or logs

### Feature Requests

For feature requests, please include:

- **Educational value**: How does this enhance learning?
- **Use case**: Specific scenario where this would be useful
- **Implementation ideas**: Any thoughts on how to implement
- **Trading concepts**: What trading strategies would this support?
- **Risk considerations**: Any risk management implications

### Issue Labels

We use the following labels to categorize issues:

- `bug`: Something isn't working correctly
- `enhancement`: New feature or improvement
- `documentation`: Documentation improvements
- `educational`: Related to educational content
- `testing`: Testing improvements
- `performance`: Performance optimization
- `good-first-issue`: Good for newcomers
- `help-wanted`: Community help needed

## 🏆 Recognition

Contributors will be recognized in several ways:

- **Contributors List**: Added to project contributors
- **Release Notes**: Major contributions highlighted in releases
- **Educational Impact**: Contributions that enhance educational value will be specially noted

## 📞 Getting Help

If you need help with contributions:

- **GitHub Issues**: Create an issue with the `help-wanted` label
- **Strategy Questions**: Reference the [Strategy Guide](earnings_iv_crush_strategy_complete_playbook.md)
- **Technical Questions**: Check existing issues and documentation

## ⚖️ Legal and Educational Notice

### Important Disclaimers

- **Educational Purpose**: All contributions must maintain the educational focus
- **No Financial Advice**: Code and documentation must not provide financial advice
- **Risk Warnings**: Include appropriate risk disclaimers in financial calculations
- **Data Sources**: Ensure data sources are properly attributed and legal to use

### License Agreement

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (Educational Use License).

---

## 🙏 Thank You!

Thank you for contributing to the Advanced Options Trading Calculator! Your contributions help make options education more accessible and comprehensive for learners worldwide.

**Remember**: This is an educational project designed to help people learn about options trading concepts and risk management. All contributions should enhance this educational mission while maintaining the highest standards of code quality and professional presentation.