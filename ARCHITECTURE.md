# Architecture

This document describes the high-level architecture of `template-repo`.
Read it first to find your way around the code. It explains *where things are*
and *why*, not *how* each function works: that belongs in docstrings.

Keep it short, and update it when you add, move or remove a top-level module.

## Bird's eye view

TODO: replace with what the project does, its inputs and outputs, and the main
flow. The template only has a command-line entry point that prints a greeting:

```
user ──> template-repo (CLI) ──> template_repo.cli.main() ──> stdout
```

## Code map

| Path                    | Role                                                       |
| ----------------------- | ---------------------------------------------------------- |
| `src/template_repo/`    | The installable package.                                   |
| `src/template_repo/cli.py` | Entry point of the `template-repo` command.             |
| `src/template_repo/config.py` | Settings, read from the environment and `.env`.      |

TODO: add a row for each top-level module of the project.
