---
description: 'Test conventions that ruff does not check'
paths: ['**/tests/**/*.py']
---
# Python Testing

- Plain `test_*` functions, no classes; one behaviour per test, named after it
  (`test_rejects_negative_altitude`, not `test_validate`); vary inputs with `parametrize`.
- Each test catches a bug you can name, and every plausible bug in the code you changed
  (wrong constant, flipped comparison, off-by-one, dropped branch, unhandled
  empty/zero/boundary/NaN/bad input) fails a test. Constants, trivial getters and library
  behaviour need no test.
- Test through the public interface: a behaviour-preserving refactor keeps tests green.
- Expected values come from outside the code (hand-computed, a reference, the spec), never
  from its own logic or helpers.
- Assert the value or effect; `is not None`, `isinstance`, "it ran" or "the mock was called"
  alone prove nothing.
- Floats: `pytest.approx`/`assert_allclose`, tolerance justified by the computation, never `==`.
- Mock only what you don't own (network, services, clock); otherwise real objects,
  `tmp_path`, `monkeypatch`.
- Deterministic: seeded randomness, no wall clock or test-order dependence.
- A clear invariant (round-trip, idempotence, monotonicity) earns a Hypothesis property test.
