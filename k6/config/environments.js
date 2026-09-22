// Resolves the target and auth for a k6 run from the SAME .env values
// ApiLibrary uses — k6 is a separate CLI (not part of `uv sync`), so these
// must be exported into the shell environment before `k6 run` (see
// docs/performance-testing-guide.md for the one-liners).
//
//   API_BASE_URL  — base for JSON endpoints (mirrors libraries/api_library.py)
//   API_COOKIES   — raw `Cookie` header captured by a real browser login;
//                    the app is an SPA + SSO with no server-side login form,
//                    so k6 CANNOT log in on its own — it reuses the cookie
//                    ApiLibrary already captured. See k6/utils/auth.js.
//   K6_ENV        — optional label (dev|staging|prod), defaults to "local"

export const ENV_NAME = __ENV.K6_ENV || 'local';

export const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:3000';

if (!__ENV.API_BASE_URL) {
  console.warn(
    'API_BASE_URL not set — defaulting to http://localhost:3000. ' +
    'Export it from .env before running (see docs/performance-testing-guide.md).'
  );
}
