// Reuses the browser-captured session cookie the same way ApiLibrary does
// (libraries/api_library.py: `_build_session`). k6 has no browser and this
// app has no server-side login form, so it can't authenticate on its own —
// it just replays the raw `Cookie` header ApiLibrary already captured and
// wrote to .env as API_COOKIES.
//
// If requests start coming back 401/302-to-login mid-run, the cookie expired:
// re-run `uv run pytest tests/api/test_example_api.py -m api` (or call
// `api_library.login_and_get_cookies()`) to mint a fresh one, then re-export
// API_COOKIES before the next k6 run.

export function authHeaders() {
  const cookie = __ENV.API_COOKIES || '';
  if (!cookie) {
    throw new Error(
      'API_COOKIES is not set. k6 reuses the cookie captured by ApiLibrary — ' +
      'export it from .env before running (see docs/performance-testing-guide.md).'
    );
  }
  return {
    Cookie: cookie,
    Accept: 'application/json',
  };
}
