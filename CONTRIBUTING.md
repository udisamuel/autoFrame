# Contributing to autoFrame

Thank you for considering contributing to autoFrame! This document outlines the process and guidelines for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. Please be kind and constructive in your interactions with others.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- A clear, descriptive title
- A detailed description of the issue, including steps to reproduce
- Expected behavior vs actual behavior
- Screenshots if applicable
- Environment details (OS, Python version, browser version if UI-related)
- Possible solutions if you have any in mind

### Suggesting Enhancements

If you have ideas for new features or improvements, please create an issue with:

- A clear, descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples, mockups, or use cases
- Why this enhancement would be useful to most users

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Ensure tests pass
5. Update documentation if necessary
6. Commit your changes (`git commit -m 'Add some feature'`)
7. Push to the branch (`git push origin feature/your-feature-name`)
8. Open a Pull Request

#### Pull Request Guidelines

- Follow the project's coding style and conventions
- Include tests for new functionality
- Update documentation for API changes
- Keep pull requests focused on a single topic
- Reference any relevant issues in your PR description

## Development Setup

1. Clone the repository
```bash
git clone <repository-url>
cd autoFrame
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers
```bash
playwright install
```

5. Run tests to verify setup
```bash
pytest
```

## Testing Guidelines

- All new code should have appropriate tests
- Tests should be independent of each other
- Mock external services when testing
- Aim for high code coverage, but prioritize meaningful tests over coverage percentage
- Use appropriate markers for different types of tests (API, UI, database, etc.)

## Documentation Guidelines

- Use docstrings for all public classes and methods
- Follow the existing documentation style
- Keep comments up to date when changing code
- Add examples for complex functionality

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Keep functions and methods focused on a single responsibility
- Use meaningful names for variables, functions, and classes
- Format your code with appropriate tools before submitting

## License

By contributing to autoFrame, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions?

If you have any questions about contributing, feel free to open an issue for clarification.

Thank you for helping make autoFrame better!
