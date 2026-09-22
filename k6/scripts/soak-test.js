// Soak test — moderate load sustained for hours. Answers "does anything
// degrade over time?" (memory leaks, connection-pool exhaustion, log/disk
// growth). NOTE: this runs long enough that the captured session cookie
// (API_COOKIES) may expire mid-run on apps with short SSO sessions — check
// the app's session TTL before scheduling a long soak.

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../config/environments.js';
import { authHeaders } from '../utils/auth.js';
import { handleSummaryReport } from '../utils/report.js';
import { DEFAULT_THRESHOLDS } from '../thresholds/default-thresholds.js';

export const options = {
  stages: [
    { duration: '5m', target: 50 },
    { duration: '4h', target: 50 },
    { duration: '5m', target: 0 },
  ],
  thresholds: DEFAULT_THRESHOLDS,
};

export default function () {
  const res = http.get(`${BASE_URL}/`, { headers: authHeaders() });
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}

export function handleSummary(data) {
  return handleSummaryReport('soak', data);
}
