---
description: 'Python conventions that ruff and mypy do not check'
paths: ['**/*.py', '**/*.ipynb']
---
# Python Coding Standards

- Abstract at the third use, not before; profile before optimising.
- Intent shows through names, types and structure; comment only what the code can't say.
  Comments and docstrings describe the code as it is, never its history ("used to",
  "previously", "now does"): that belongs in the commit message.
- Keep logic pure; isolate I/O at the edges, so tests need no mocks.
- Docstrings: numpy style, never `Args:`; the public API documents `Parameters`,
  `Returns`/`Yields`, and `Raises` when it raises.
- Arrays: `npt.NDArray` with an abstract dtype (`np.floating`, `np.integer`, `np.number`…),
  a concrete one (`np.float64`) only when precision matters; `npt.ArrayLike` for inputs;
  xarray as `xr.Dataset` / `xr.DataArray`.
- Optional dependencies use `lazy import x` (PEP 810), not `importlib` or `TYPE_CHECKING`.
- No magic values: `Enum` for fixed sets, `UPPER_SNAKE_CASE` module constants, dataclasses or
  Pydantic models for structured configuration, not raw dicts.
- Operational output goes through `logging.getLogger(__name__)`, never `print()`; never log
  confidential or personal data.
- Errors: custom exceptions for domain errors, `ValueError` for invalid input; messages carry
  the context.
- Configuration from environment variables (`.env` in dev); secrets in a secret manager.
- Validate user and external input (files, requests, environment) where it enters the code.
