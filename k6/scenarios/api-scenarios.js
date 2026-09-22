// Template for real endpoint coverage — copy this when you have more than
// one flow to hit in the same run. Replace the placeholder paths with real
// endpoints (same ones your tests/api/ suite exercises) and tag thresholds
// per scenario so a slow endpoint doesn't get hidden inside an averaged one.

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../config/environments.js';
import { authHeaders } from '../utils/auth.js';
import { handleSummaryReport } from '../utils/report.js';

export const options = {
  scenarios: {
    browse: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },
        { duration: '5m', target: 50 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browse',
    },
    health_check: {
      executor: 'constant-vus',
      vus: 5,
      duration: '9m',
      exec: 'healthCheck',
    },
  },
  thresholds: {
    'http_req_duration{scenario:browse}': ['p(95)<300'],
    'http_req_duration{scenario:health_check}': ['p(95)<100'],
    http_req_failed: ['rate<0.01'],
  },
};

// TODO: replace `/orders` with a real endpoint from tests/api/.
export function browse() {
  const res = http.get(`${BASE_URL}/orders?status=open`, { headers: authHeaders() });
  check(res, { 'orders status is 200': (r) => r.status === 200 });
  sleep(2);
}

export function healthCheck() {
  const res = http.get(`${BASE_URL}/health`, { headers: authHeaders() });
  check(res, { 'health status is 200': (r) => r.status === 200 });
  sleep(1);
}

export function handleSummary(data) {
  return handleSummaryReport('api-scenarios', data);
}
