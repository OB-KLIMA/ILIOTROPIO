.DEFAULT_GOAL := help
.PHONY: help init-dev init-prod lint test security check docs promote clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

init-dev: ## Set up a dev environment: all dependency groups, git hooks, .env
	uv sync
	uv run pre-commit install
	@test -f .env || { cp .env.example .env && echo "Created .env from .env.example: fill in the values."; }

init-prod: ## Set up production: runtime dependencies only, exactly as in uv.lock
	@test -f .env || { echo "Missing .env: copy .env.example to .env and fill in the values."; exit 1; }
	uv sync --locked --no-default-groups --no-editable

lint: ## Run all pre-commit hooks on all files (ruff, mypy, gitleaks...)
	uv run pre-commit run --all-files

test: ## Run the test suite with coverage
	uv run pytest --cov --cov-report=term-missing

security: ## Scan the code (bandit) and the dependencies (pip-audit) for vulnerabilities
	uv sync --all-groups
	uv run --with bandit bandit -r src/ tests/ -c pyproject.toml --severity-level medium
	uv run --with pip-audit pip-audit

check: lint test security ## Run everything CI runs

docs: ## Serve the documentation with live reload on http://127.0.0.1:8000
	uv run --group docs mkdocs serve

promote: ## Release: fast-forward prod to dev and tag it v<version> (from pyproject.toml)
	git fetch origin --tags
	@git merge-base --is-ancestor origin/prod origin/dev || { echo "prod has commits that are not in dev: merge them into dev first."; exit 1; }
	@tag=v$$(git show origin/dev:pyproject.toml | sed -n 's/^version = "\(.*\)"/\1/p' | head -1); \
	if git rev-parse -q --verify "refs/tags/$$tag" >/dev/null; then \
		echo "$$tag already exists: bump the version on dev first (uv version --bump minor)."; exit 1; \
	fi; \
	git tag -a "$$tag" -m "$$tag" origin/dev && git push origin origin/dev:refs/heads/prod "$$tag"

clean: ## Remove caches and build artifacts
	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage htmlcov build dist site
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
