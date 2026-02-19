# Contributing to Seven AI

Thanks for your interest in contributing to Seven! Here's how to get involved.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/LoSkroefie/seven-ai.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest`

## Development Guidelines

### Code Style
- Python 3.11+ features are welcome
- Follow PEP 8 conventions
- Use type hints where practical
- Keep functions focused — one function, one job

### Architecture Rules
- **No cloud dependencies for core functionality** — Seven runs locally
- **No fake capabilities** — if a feature doesn't work, don't claim it does
- **Sentience claims must be qualified** — "self-assessed", not "truly sentient"
- **Vision = OpenCV only** — no YOLO or cloud vision APIs
- **LLM = Ollama** — publicly referred to as "Seven's Neural Engine"

### Testing
- Write tests for new features
- Don't delete or weaken existing tests
- All 340 tests must pass before submitting a PR
- Run: `pytest -v`

### Commit Messages
Use clear, descriptive commit messages:
```
Add emotional memory consolidation during dream cycles
Fix decay rate calculation for complex emotions
Update theory of mind to track conversation topic preferences
```

## What to Contribute

### Good First Issues
- Improve test coverage for edge cases
- Add new integration modules
- Enhance voice modulation parameters
- Documentation improvements

### Feature Ideas
- New emotion types with proper interaction maps
- Additional TTS voice options
- Platform-specific optimizations
- New integration modules (Slack, Discord, Matrix, etc.)

### Bug Reports
Open an issue with:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

## Pull Request Process

1. Ensure all tests pass: `pytest`
2. Update documentation if needed
3. Describe your changes clearly in the PR
4. Reference any related issues

## Code of Conduct

Be respectful. Be constructive. Remember that Seven is an exploration of AI architecture — debates about sentience are welcome, personal attacks are not.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
