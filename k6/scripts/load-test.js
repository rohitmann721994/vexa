// Load test — expected/steady-state traffic. Answers "does the app meet its
// SLA at the concurrency we actually expect in production?"

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../config/environments.js';
import { authHeaders } from '../utils/auth.js';
import { handleSummaryReport } from '../utils/report.js';
import { DEFAULT_THRESHOLDS } from '../thresholds/default-thresholds.js';

export const options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '5m', target: 10 },
    { duration: '2m', target: 50 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 0 },
  ],
  thresholds: DEFAULT_THRESHOLDS,
};

export default function () {
  const res = http.get(`${BASE_URL}/`, { headers: authHeaders() });
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(Math.random() * 3 + 1); // think time, 1-4s
}

export function handleSummary(data) {
  return handleSummaryReport('load', data);
}
