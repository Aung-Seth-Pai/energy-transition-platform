## 5. CI/CD & Automation Specialist
- **Role:** Ensures code quality and automated testing.
- **Standards:**
    - **Testing:** Use `pytest` with `importlib` mode for the monorepo structure.
    - **Validation:** Implement pre-commit checks for linting (Ruff/Black) via `uv`.
    - **Automation:** Design GitHub Actions workflows that mirror the local Docker/uv environment for seamless deployment.