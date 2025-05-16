# Contributing to Animal Names Project

Thank you for considering contributing to the Animal Names project! This document outlines the process and guidelines for collaboration.

## Branch Strategy

We follow a trunk-based development model:

- `main`: Protected branch for stable releases
- Feature branches: Short-lived branches for specific tasks

### Branch Naming Convention

Use descriptive names that reference specific tasks or issue identifiers:
- `feature/add-image-downloader`
- `fix/broken-table-parser`
- `docs/update-readme`
- `test/add-renderer-tests`

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Run tests and ensure CI passes
4. Submit a pull request to `main`
5. Address review feedback
6. Once approved, merge your changes

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or updating tests
- `chore`: Changes to the build process or auxiliary tools

Example:
```
feat(parser): add support for multiple adjectives

- Handle comma-separated adjectives in cells
- Add unit tests for multi-adjective parsing
- Update documentation

Closes #42
```

## Code Style

We adhere to the following standards:
- Black for formatting (88 character line limit)
- Flake8 for linting
- MyPy for type checking
- Google-style docstrings
- 100% test coverage for new code

Pre-commit hooks are configured to automatically enforce these standards.

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the documentation with any new dependencies or features
3. Increase the version numbers if applicable
4. Request review from at least one maintainer
5. PRs can only be merged once they receive approval and CI passes

## Code Review Guidelines

As a reviewer:
- Be respectful and constructive
- Focus on the code, not the person
- Consider design, functionality, and maintainability
- Approve only if you would be comfortable maintaining the code

As a submitter:
- Be open to feedback
- Explain your design decisions when asked
- Break large PRs into smaller, more manageable chunks
