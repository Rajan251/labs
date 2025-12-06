# Contributing to Video Platform

We welcome contributions! Please follow these guidelines.

## Development Workflow

1.  **Fork & Clone**: Fork the repo and clone it locally.
2.  **Branching**: Create a feature branch `feature/my-feature` or `fix/issue-id`.
3.  **Setup**: Run `make setup` to install dependencies.
4.  **Run**: Run `make up` to start the local stack.
5.  **Test**: Run `make test` before pushing.
6.  **Lint**: Run `make lint` to ensure code quality.

## Pull Requests

-   Provide a clear description of changes.
-   Link to relevant issues.
-   Ensure CI checks pass.

## Code Style

-   **TypeScript**: Follow ESLint rules.
-   **Python**: Follow PEP 8.
-   **Go**: Follow `gofmt`.

## Release Process

We use Semantic Versioning.
-   `fix:` -> Patch
-   `feat:` -> Minor
-   `BREAKING CHANGE:` -> Major
