// Stress test — push well past expected load in steps to find the breaking
// point and how the app degrades (errors climb? latency climbs? both?).

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../config/environments.js';
import { authHeaders } from '../utils/auth.js';
import { handleSummaryReport } from '../utils/report.js';
import { RELAXED_THRESHOLDS } from '../thresholds/default-thresholds.js';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 300 },
    { duration: '5m', target: 300 },
    { duration: '2m', target: 400 },
    { duration: '5m', target: 400 },
    { duration: '10m', target: 0 },
  ],
  thresholds: RELAXED_THRESHOLDS,
};

export default function () {
  const res = http.get(`${BASE_URL}/`, { headers: authHeaders() });
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}

export function handleSummary(data) {
  return handleSummaryReport('stress', data);
}
