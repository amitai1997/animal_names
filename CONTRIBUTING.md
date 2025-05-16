# Contributing to Animal Names Project

Thank you for considering contributing to the Animal Names project! This document outlines the process and guidelines for collaboration.

## Branch Strategy

We follow a trunk-based development model:

- `main`: Protected branch for stable releases
- Feature branches: Short-lived branches for specific tasks

### Branch Naming Convention

Use descriptive names that reference specific tasks or issue identifiers:
- `day1-feature`, `day2-feature`, etc. for day-specific tasks
- `feature/add-image-downloader`
- `fix/broken-table-parser`
- `docs/update-readme`
- `test/add-renderer-tests`

## Development Workflow

1. Create a feature branch from `main`
   ```bash
   python /root/git_workflow.py create-branch branch-name
   ```

2. Make your changes with clear, atomic commits
   ```bash
   python /root/git_workflow.py commit "your commit message"
   ```

3. Run tests and ensure CI passes
   ```bash
   python /root/project.py test -v
   ```

4. Format and lint your code
   ```bash
   python /root/project.py format
   python /root/project.py lint
   ```

5. Submit a pull request to `main`
6. Address review feedback
7. Once approved, merge your changes

## Development Helper Scripts

We provide several helper scripts to simplify development:

### Project Management Script (`/root/project.py`)

```bash
# Run tests
python /root/project.py test

# Run verbose tests
python /root/project.py test -v

# Run tests with a specific keyword
python /root/project.py test -k "normalize"

# Run linting
python /root/project.py lint

# Format code
python /root/project.py format

# Install dependencies
python /root/project.py install

# Clean temporary files
python /root/project.py clean
```

### Git Workflow Script (`/root/git_workflow.py`)

```bash
# Check status
python /root/git_workflow.py status

# Commit changes
python /root/git_workflow.py commit "your commit message"

# Create a new branch
python /root/git_workflow.py create-branch branch-name

# Checkout a branch
python /root/git_workflow.py checkout branch-name

# Push changes
python /root/git_workflow.py push

# Pull changes
python /root/git_workflow.py pull
```

### Day Runner Script (`/root/day_runner.py`)

To automate day-specific tasks:

```bash
# Run tasks for a specific day (1-6)
python /root/day_runner.py <day_number>
```

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
