---
description: 'How to work on any task: think first, stay in scope, verify.'
---
# Working Method

Caution over speed; on trivial tasks, use judgment.

## Think before coding
- State your assumptions; if the request is unclear or has several readings, name them and
  ask; don't pick silently.
- If a simpler approach exists, say so; push back when warranted.

## Stay in scope
- Every changed line traces to the request: no extra features, configurability, handling of
  impossible cases, or edits to adjacent code, comments or formatting; don't refactor what
  isn't broken.
- Mention unrelated dead code, don't delete it; remove only what your own change made unused.

## Verify
- Test first: write the test (for a bug, one that reproduces it), watch it fail for the
  expected reason, make it pass, then tidy what you wrote. Docs, config and CI need no test.
- When a test fails, fix the code: don't edit expected values, loosen tolerances, skip,
  `xfail` or special-case test inputs; if the test is wrong, say why first.
- For a multi-step task, state a short plan with a check per step.
- Done means `make check` passes (same as CI); faster loop: `make test`, `make lint`.
