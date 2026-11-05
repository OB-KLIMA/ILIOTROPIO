# Contributing

Thanks for contributing. This guide covers the setup, the day-to-day workflow
and what a reviewer expects from a pull request.

## Setup

Requirements: [uv](https://docs.astral.sh/uv/), Git and `make`. uv installs
the right Python version (see `.python-version`) by itself.

```bash
git clone git@github.com:klima-aero/template-repo.git
cd template-repo
make init-dev                 # dependencies, git hooks, .env from .env.example
```

Then fill in the values in `.env`, and check that everything works:

```bash
uv run template-repo          # runs the command-line entry point
make check                    # pre-commit hooks, tests, security scan, like CI
```

Run `make` alone to list the available recipes. On a production machine, use
`make init-prod` instead: it installs the runtime dependencies only, exactly
as pinned in `uv.lock`.

## Branches

| Branch | Role                                                            |
| ------ | --------------------------------------------------------------- |
| `dev`  | Default branch. Every change starts from it and comes back to it through a pull request. |
| `prod` | Protected. What runs in production. Always **behind or equal to** `dev`, never ahead. |

```
feat/x, fix/y ──PR──▶ dev ──make promote (fast-forward)──▶ prod
```

- Branch from `dev`, open the pull request against `dev`.
- Never commit, merge or open a work branch on `prod`.
- To release, run `make promote`: it moves `prod` forward to the current
  `dev`, tags it `v<version>`, and refuses if `prod` has a commit that `dev`
  doesn't, or if the tag already exists. A pull request
  from `dev` to `prod` is fine for review, but don't merge it with the GitHub
  button: the merge commit would exist only on `prod`. `make promote` closes it.
- Hotfix: branch from `dev`, merge into `dev`, then `make promote`.

## Workflow

1. Open or pick an issue, and assign it to yourself.
2. Create a branch from `dev`.
3. Commit small, focused changes. A commit-msg hook rejects messages that
   don't follow the format in the rules.
4. Push and open a pull request **against `dev`**. Fill in the template.
5. Address the review comments, then merge once approved and CI is green.
   Delete the branch after merging.

Never push directly to `dev`, and never change `prod` other than with
`make promote`.

## Releases

1. In a pull request to `dev`, bump the version with
   `uv version --bump patch|minor|major` (SemVer), and move the
   `[Unreleased]` entries of `CHANGELOG.md` under a new `[x.y.z] - YYYY-MM-DD`
   heading.
2. Once it is merged, a maintainer runs `make promote`. It fast-forwards
   `prod` to the current `dev`, so `prod` never contains a commit that `dev`
   doesn't have, and tags the release `vx.y.z`.

Everything merged into `dev` goes out together: don't merge into `dev` what is
not ready to ship.

## Standards

The coding, testing, branch and commit standards are in
[`.claude/rules/`](.claude/rules/): they apply to everyone, not only to
Claude Code. The pre-commit hooks enforce most of them.

## Tests

- Mirror the layout of `src/template_repo/` in `tests/`.
- A bug fix comes with a test that fails without the fix.
- Run a single test with `uv run pytest tests/unit/test_x.py::test_name`.

## Documentation

`make docs` serves the documentation (MkDocs, in `docs/`) on
http://127.0.0.1:8000. The API reference is generated from the docstrings.

## Dependencies

- Add a runtime dependency with `uv add <package>`, a dev-only one with
  `uv add --group dev|test|docs <package>`. Never use pip: it bypasses `uv.lock`.
- Commit `pyproject.toml` and `uv.lock` together.
- Dependabot opens weekly update PRs: review them like any other PR.

## Pull requests

A good PR:

- does one thing, and stays small enough to review in under 30 minutes;
- explains *why* in its description, and how to test it;
- adds a line under `[Unreleased]` in `CHANGELOG.md` if users will notice it;
- updates the docs it affects (`README.md`, `ARCHITECTURE.md`, docstrings);
- passes CI.

As a reviewer, answer within one working day. Approve, request changes, or
say when you will look at it.

## Reporting bugs and ideas

Use the issue templates: **Bug report** or **Feature request**.
