// Smoke test — minimal load, just prove the target endpoint(s) work at all.
// Run this before load/stress/spike/soak; if smoke fails, the bigger tests
// will fail for the same reason and just cost more time to tell you so.

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../config/environments.js';
import { authHeaders } from '../utils/auth.js';
import { handleSummaryReport } from '../utils/report.js';
import { SMOKE_THRESHOLDS } from '../thresholds/default-thresholds.js';

export const options = {
  vus: 1,
  duration: '1m',
  thresholds: SMOKE_THRESHOLDS,
};

export default function () {
  const res = http.get(`${BASE_URL}/`, { headers: authHeaders() });
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}

export function handleSummary(data) {
  return handleSummaryReport('smoke', data);
}
