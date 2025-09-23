# Contributing to VaultSentinel

Thank you for your interest in contributing to VaultSentinel! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for containerized development)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/vaultsentinel.git
   cd vaultsentinel
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Run Tests**
   ```bash
   pytest tests/
   ```

## 🏗️ Architecture Overview

VaultSentinel follows a modular, plugin-first architecture:

- **Core**: Agent loop, configuration, domain models
- **Detectors**: Secret detection engines (regex, entropy, ML)
- **Connectors**: Data source integrations (GitHub, GitLab, etc.)
- **Remediation**: Action handlers (Slack, AWS, custom)
- **API**: FastAPI service with REST endpoints
- **UI**: Web dashboard for findings management

## 🔌 Plugin Development

### Creating a New Detector

1. **Implement the Detector Interface**
   ```python
   from core.interfaces import Detector, DetectionContext
   from core.models import Finding, SecretKind
   
   class MyDetector:
       name = "my_detector"
       
       def detect(self, context: DetectionContext) -> Iterable[Finding]:
           # Your detection logic here
           pass
       
       def is_enabled(self) -> bool:
           return True
   ```

2. **Register the Detector**
   ```python
   from core.interfaces import register_detector
   
   @register_detector
   class MyDetector:
       # ... implementation
   ```

3. **Add Tests**
   ```python
   def test_my_detector():
       detector = MyDetector()
       context = DetectionContext(...)
       findings = list(detector.detect(context))
       assert len(findings) > 0
   ```

### Creating a New Connector

1. **Implement the Connector Interface**
   ```python
   from core.interfaces import Connector, DetectionContext
   
   class MyConnector:
       name = "my_connector"
       
       def connect(self) -> bool:
           # Test connection to data source
           pass
       
       def fetch_changes(self, since: Optional[str] = None) -> Iterable[DetectionContext]:
           # Fetch changes from data source
           pass
       
       def is_enabled(self) -> bool:
           return True
   ```

2. **Register the Connector**
   ```python
   from core.interfaces import register_connector
   
   @register_connector
   class MyConnector:
       # ... implementation
   ```

### Creating a New Remediation Handler

1. **Implement the Remediation Handler Interface**
   ```python
   from core.interfaces import RemediationHandler
   from core.models import Finding
   
   class MyRemediationHandler:
       name = "my_remediation"
       
       def can_handle(self, finding: Finding) -> bool:
           # Check if this handler can remediate the finding
           pass
       
       def remediate(self, finding: Finding) -> Dict[str, Any]:
           # Execute remediation action
           pass
       
       def is_enabled(self) -> bool:
           return True
   ```

2. **Register the Handler**
   ```python
   from core.interfaces import register_remediation_handler
   
   @register_remediation_handler
   class MyRemediationHandler:
       # ... implementation
   ```

## 🧪 Testing Guidelines

### Unit Tests

- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names
- Test both success and failure cases

### Integration Tests

- Test plugin registration and discovery
- Test end-to-end workflows
- Test error handling and edge cases

### E2E Tests

- Test with real repositories (use test fixtures)
- Verify detection → alerting → persistence flow
- Test remediation actions (with stubbed responses)

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=packages tests/

# Run specific test file
pytest tests/test_regex_detector.py

# Run with verbose output
pytest -v tests/
```

## 📝 Code Style

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Use docstrings for classes and functions
- Keep functions small and focused

### Formatting

We use automated formatting tools:

```bash
# Format code with black
black packages/ tests/ main.py

# Sort imports with isort
isort packages/ tests/ main.py

# Check style with flake8
flake8 packages/ tests/ main.py

# Type checking with mypy
mypy packages/ main.py
```

### Pre-commit Hooks

Set up pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

## 📋 Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
2. **Check Style**: Run linting tools
3. **Update Documentation**: Update README if needed
4. **Add Tests**: Include tests for new functionality

### PR Template

When creating a pull request, include:

- **Description**: What changes were made and why
- **Testing**: How the changes were tested
- **Breaking Changes**: Any breaking changes and migration steps
- **Screenshots**: For UI changes
- **Checklist**: Ensure all items are completed

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Code Review**: At least one maintainer reviews the code
3. **Testing**: Manual testing of new features
4. **Approval**: Maintainer approves and merges

## 🐛 Bug Reports

When reporting bugs, include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, dependencies
- **Logs**: Relevant log output

## 💡 Feature Requests

When requesting features, include:

- **Use Case**: Why this feature is needed
- **Proposed Solution**: How you think it should work
- **Alternatives**: Other solutions you've considered
- **Additional Context**: Any other relevant information

## 🔒 Security

### Security Issues

For security-related issues:

1. **DO NOT** create public issues
2. Email security@vaultsentinel.io
3. Include detailed information about the vulnerability
4. Allow time for response before public disclosure

### Security Best Practices

- Never commit secrets or credentials
- Use environment variables for configuration
- Follow principle of least privilege
- Validate all inputs
- Use secure coding practices

## 📚 Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Include type hints for better IDE support
- Add comments for complex logic
- Keep documentation up to date

### User Documentation

- Update README.md for new features
- Add examples and use cases
- Include configuration options
- Document breaking changes

## 🏷️ Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## 🎯 Roadmap

### Short Term (Next 3 months)
- Additional connectors (GitLab, Jenkins)
- Enhanced detection patterns
- Improved UI/UX
- Performance optimizations

### Medium Term (3-6 months)
- ML-based detection
- Multi-tenant support
- Advanced remediation
- Compliance reporting

### Long Term (6+ months)
- Enterprise features
- Cloud-native deployment
- Advanced analytics
- Integration ecosystem

## 🤝 Community

### Getting Help

- **GitHub Discussions**: For questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check the wiki for detailed guides
- **Code Review**: Learn from existing code and PRs

### Contributing Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Follow the code of conduct

## 📄 License

By contributing to VaultSentinel, you agree that your contributions will be licensed under the MIT License.

## 🙏 Acknowledgments

Thank you to all contributors who help make VaultSentinel better! Your contributions are valuable and appreciated.

---

For any questions about contributing, please open a discussion or contact the maintainers.
