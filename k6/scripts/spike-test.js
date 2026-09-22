// Spike test — sudden burst far above normal load, then recovery. Answers
// "does the app survive a traffic spike, and does it recover after?"

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../config/environments.js';
import { authHeaders } from '../utils/auth.js';
import { handleSummaryReport } from '../utils/report.js';
import { RELAXED_THRESHOLDS } from '../thresholds/default-thresholds.js';

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // normal load
    { duration: '10s', target: 500 }, // spike
    { duration: '3m', target: 500 },  // hold
    { duration: '10s', target: 10 },  // recovery
    { duration: '3m', target: 10 },   // observe recovery
    { duration: '1m', target: 0 },
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
  return handleSummaryReport('spike', data);
}
