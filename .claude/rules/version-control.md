---
description: 'Branches, commits, versions, changelog and docs.'
---
# Version Control

- Branch from `dev` (`feat/…`, `fix/…`, `docs/…`) and open a PR against `dev`; never push to
  `dev` or `prod`: `prod` moves only through `make promote`.
- Conventional Commits (a hook checks the format): imperative, lowercase description, no
  final period, first line under 72 chars; body says *why*; footer `Closes #42`; one logical
  change per commit.
- Types beyond `feat`/`fix`: `build` for `pyproject.toml` and `uv.lock`, `ci` for
  `.github/workflows/`, `docs` for documentation, `chore` for the rest outside `src/` and
  `tests/`.
- Versions follow SemVer; a change users will notice goes under `[Unreleased]` in
  `CHANGELOG.md` (Keep a Changelog).
- Update the docs a change affects: `README.md`, `docs/` (MkDocs), docstrings, and
  `ARCHITECTURE.md` when a top-level module is added, moved or removed.
- Keep every doc tight (README, ARCHITECTURE, CONTRIBUTING, CHANGELOG, `docs/`, docstrings):
  only what the reader needs, no filler or restating the code.
