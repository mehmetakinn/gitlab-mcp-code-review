# Contributing to GitLab Code Review MCP

Thank you for considering contributing to GitLab Code Review MCP! Here's how you can help:

## Development Process

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up the development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. Make your changes
5. Run linting and tests:
   ```bash
   black .
   isort .
   mypy server.py
   pytest
   ```
6. Commit your changes with meaningful commit messages:
   ```bash
   git commit -m "Add some amazing feature"
   ```
7. Push to your branch:
   ```bash
   git push origin feature/amazing-feature
   ```
8. Open a Pull Request

## Pull Request Guidelines

- Update the README.md if needed
- Keep pull requests focused on a single change
- Write tests for your changes when possible
- Document new code based using docstrings
- End all files with a newline

## Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 