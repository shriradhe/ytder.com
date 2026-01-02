# Contributing to Video Download Service

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Testing](#testing)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/yourusername/ytder-python-backend.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`

## Development Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**:
   ```bash
   python start.py
   # or
   python main.py
   ```

## Making Changes

### Project Structure

- **Source code**: `src/` directory
- **Frontend**: `static/` directory
- **Documentation**: `docs/` directory
- **Tests**: `tests/` directory

### Code Organization

- Follow existing code patterns
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

## Code Style

- Follow PEP 8 style guide
- Use Black for code formatting (line length: 100)
- Use meaningful variable and function names
- Add comments for complex logic

### Formatting

```bash
# Install dev dependencies
pip install black flake8 mypy

# Format code
black src/ main.py

# Check linting
flake8 src/ main.py

# Type checking
mypy src/ main.py
```

## Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Add tests to `tests/` directory

```bash
# Run tests
pytest tests/
```

## Submitting Changes

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Description of your changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**:
   - Provide a clear description
   - Reference any related issues
   - Include screenshots if UI changes

## Commit Message Format

- `Add:` - New feature
- `Fix:` - Bug fix
- `Update:` - Update existing feature
- `Refactor:` - Code refactoring
- `Docs:` - Documentation changes
- `Style:` - Code style changes
- `Test:` - Test additions/changes

Example: `Add: SEO management feature in admin panel`

## Questions?

Feel free to open an issue for questions or discussions.

Thank you for contributing! 🎉

