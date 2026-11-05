# ILIOTROPIO

[![CI](https://github.com/OB-KLIMA/ILIOTROPIO/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/OB-KLIMA/ILIOTROPIO/actions/workflows/ci.yml)
[![Python 3.15](https://img.shields.io/badge/python-3.15-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

TODO: replace the title and this line with what the project does, and for whom.

- **Notion**: TODO: link to the project's Notion page
- **Slack**: TODO: `#my-project`

## Using this template

> **Template only: delete this section** once these steps are done.

Everything else in the docs is meant to stay as is. The only project-specific
parts are the `TODO`s (`git grep -n TODO` lists them) and the code in `src/`
and `tests/`.

1. **Create the repository**: on GitHub, **Use this template > Create a new
   repository**. Then create `prod` from `dev`:
   `git push origin origin/dev:refs/heads/prod`.
2. **Rename the package** (replace `my-project` / `my_project` with your name):
   ```bash
   git mv src/template_repo src/my_project
   git grep -l -e template-repo -e template_repo \
     | xargs sed -i -e 's/template-repo/my-project/g' -e 's/template_repo/my_project/g'
   uv lock
   ```
   Check the result with `git diff`: it also updates the badge URLs and the
   clone URL in `CONTRIBUTING.md`.
3. **Adapt the project-specific parts**: the `TODO`s (top of this README,
   *Bird's eye view* and *Code map* in `ARCHITECTURE.md`), `description` and
   `authors` in `pyproject.toml`, the year in `LICENSE`, the variables in
   `.env.example`. Replace the greeting in `src/<package>/cli.py` and its
   test with your code. `CONTRIBUTING.md` needs no change.
4. **Set up your environment**: `make init-dev`, then `make check` (everything
   must pass).
5. **Configure GitHub** (Settings):
   - **General**: set `dev` as the default branch.
   - **Rules > Rulesets** for `dev`: require a pull request and the status
     checks *Lint, format & type check*, *Tests* and *Security scan*; block
     force pushes.
   - **Rules > Rulesets** for `prod`: restrict updates to the maintainers,
     require the same status checks, block force pushes and deletion. Don't
     require a pull request: `prod` moves by fast-forward (`make promote`).
   - **Advanced Security**: turn on Dependabot alerts and secret scanning.
6. **Remove what you don't need**: the eslint/prettier hooks in
   `.pre-commit-config.yaml` if the project has no JS/TS code, and the unused
   ecosystems in `.github/dependabot.yml`.
7. **Create the project's Notion page and Slack channel**, named after the
   repository, and put their links at the top of this README. The Notion page
   holds the specs, decisions and meeting notes; the Slack channel is where
   the project is discussed. In the channel, run
   `/github subscribe <org>/<repo>` to get PRs, issues and releases posted
   there (needs the GitHub app for Slack).
