# pytest Patterns (Quick Reference)

Conventions this framework leans on. Keep tests thin, put reusable setup in
fixtures, and register every marker.

## Fixtures

Fixtures provide setup/teardown and shared objects. They cascade by directory
via `conftest.py`:

| Fixture | Scope | Defined in | Gives you |
|---------|-------|-----------|-----------|
| `uiLibrary` | function | `tests/conftest.py` | browser lifecycle + login; auto-closes on teardown |
| `evidence` | function | `tests/ui/conftest.py` | annotated screenshot recorder → `steps.md` |
| `api_library` | session | `tests/api/conftest.py` | authenticated `ApiLibrary` (logs in once per run) |
| `api_session` | session | `tests/api/conftest.py` | the raw authenticated `requests.Session` |

Teardown goes after `yield`:

```python
@pytest.fixture
def uiLibrary():
    lib = UiLibrary()
    yield lib
    lib.close_application()   # runs even if the test fails
```

Prefer the narrowest scope that's correct. `function` (default) gives each test
a clean slate; `session` is for expensive one-time setup like login.

## Markers

Register in `pytest.ini` before use (`--strict-markers` makes an unknown marker
an error):

```python
@pytest.mark.ui                       # browser test
@pytest.mark.api                      # API test
@pytest.mark.smoke                    # fast health check
@pytest.mark.regression               # guards a specific fix
@pytest.mark.ticket("ABC-123")        # tracker id this test verifies
@pytest.mark.slow                     # long-running
```

Run a subset with `-m`: `uv run pytest -m "ui and smoke"`,
`uv run pytest -m "not slow"`.

## Parametrize

One test, many inputs — each case reports separately:

```python
@pytest.mark.parametrize("value,expected", [
    ("", "required"),
    ("ab", "too short"),
    ("x" * 300, "too long"),
], ids=["empty", "short", "long"])
def test_validation_message(uiLibrary, value, expected):
    ...
```

## Skip / xfail

- **Skip** when a precondition isn't met (no credentials, feature off):

```python
pytestmark = pytest.mark.skipif(not os.getenv("UI_BASE_URL"), reason="not configured")
```

- **xfail (strict)** for a test that asserts a *still-broken* feature's correct
  behavior. It shows XFAIL now and hard-fails (XPASS) the moment the fix lands —
  so you never report a green PASS on a bug:

```python
@pytest.mark.xfail(strict=True, reason="ABC-123 not fixed yet")
def test_expected_behavior_once_fixed(uiLibrary):
    ...
```

## Assertions

Plain `assert` with a message that prints the observed state — a failure should
explain itself without a debugger:

```python
assert status == "Saved", f"expected 'Saved', got {status!r} at {page.url}"
```

Assert **authoritative server state** (reload the screen) rather than the
optimistic in-page result.

## Layering (non-negotiable)

- Locators + page actions → `pages/ui/<page>.py`
- Orchestration (login, navigation) → `libraries/`
- Assertions + scenario flow → `tests/`

No raw Playwright in tests; no assertions in page objects.
