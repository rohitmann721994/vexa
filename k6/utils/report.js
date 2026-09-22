// Report style: mirrors conftest.py's convention for the pytest suite — one
// timestamped, self-contained HTML file per run under reports/, plus a raw
// JSON dump for CI/trend parsing. Import handleSummaryReport from every
// script's `handleSummary(data)` export so every k6 run reports the same way
// pytest-html reports do for UI/API runs.
//
//   reports/k6_<test-name>_<timestamp>.html   — open in a browser, self-contained
//   reports/k6_<test-name>_<timestamp>.json   — raw metrics for trend analysis

import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.1.0/index.js';

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}_` +
    `${pad(d.getHours())}-${pad(d.getMinutes())}-${pad(d.getSeconds())}`
  );
}

// `name` should match the script, e.g. "smoke", "load", "stress", "spike", "soak".
export function handleSummaryReport(name, data) {
  const ts = timestamp();
  const base = `reports/k6_${name}_${ts}`;
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
    [`${base}.html`]: htmlReport(data),
    [`${base}.json`]: JSON.stringify(data, null, 2),
  };
}
