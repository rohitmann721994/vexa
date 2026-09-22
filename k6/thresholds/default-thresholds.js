// Shared pass/fail criteria so every script judges "healthy" the same way.
// Override per-script when a specific endpoint has a tighter/looser SLA —
// don't silently ship a script with no thresholds (see CLAUDE.md-style rule:
// a test without a pass/fail line is just an observation).

export const DEFAULT_THRESHOLDS = {
  http_req_duration: ['p(95)<500', 'p(99)<1000'],
  http_req_failed: ['rate<0.01'],
};

export const RELAXED_THRESHOLDS = {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],
  http_req_failed: ['rate<0.05'],
};

export const SMOKE_THRESHOLDS = {
  http_req_duration: ['p(99)<1500'],
  http_req_failed: ['rate<0.01'],
};
