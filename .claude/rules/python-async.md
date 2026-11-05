---
description: 'Async conventions, loaded with every Python file and notebook.'
paths: ['**/*.py', '**/*.ipynb']
---
# Python Async

- Async only for I/O-bound work, never into a sync codebase for one call; CPU-bound work goes
  to `concurrent.futures`/`multiprocessing`. HTTP client: `httpx`.
- Wrap unavoidable blocking calls with `asyncio.to_thread()`; handle the exceptions of every
  `asyncio.create_task()`, which are otherwise lost.
- Tests: `pytest-asyncio` with `@pytest.mark.asyncio`; FastAPI apps through
  `httpx.AsyncClient` with `ASGITransport`.
