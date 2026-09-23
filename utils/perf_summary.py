"""Builds the executive-style "results at a glance" performance report —
a tile grid (load/stress/spike/soak) with click-to-expand detail panels and
a signoff footer — from the raw k6 JSON summaries k6/utils/report.js already
writes to reports/.

This is a different report than the per-run k6-reporter HTML: that one is a
technical dump for whoever ran the test; this one is for handing to
leadership/a ticket, matching the shape of past Vexa performance write-ups.

Usage:
    uv run python utils/perf_summary.py \\
        --load reports/k6_load_2026-09-10_10-00-00.json \\
        --stress reports/k6_stress_2026-09-10_10-20-00.json \\
        --spike reports/k6_spike_2026-09-10_10-40-00.json \\
        --soak reports/k6_soak_2026-09-10_11-00-00.json \\
        --narrative k6/report_template/narrative.example.json

Any of --load/--stress/--spike/--soak may be omitted — the script then picks
the most recent matching reports/k6_<type>_*.json automatically. A test type
with no JSON found at all is left out of the grid.

The narrative file supplies the parts a person has to write (verdict
headline/sub, secondary findings, recommendations, footnotes, prepared-for) —
see k6/report_template/narrative.example.json. Everything metric-shaped (p95,
concurrency, request counts, pass/warn/fail) is computed from the JSON.
"""

import argparse
import glob
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_PATH = _ROOT / "k6" / "report_template" / "perf_summary_template.html"
_REPORTS_DIR = _ROOT / "reports"

# Static per-test-type presentation — matches the stage shapes in
# k6/scripts/*.js. Only the metrics (p95/VUs/requests/pass-fail) are computed
# from real data; everything below is fixed narrative scaffolding.
_TEST_META = {
    "load": {
        "label": "Load",
        "scenario": "Normal expected traffic, held steady",
        "sparkline": '<path d="M6,30 L21.4,4 L98.6,4 L114,30" fill="none" stroke="{color}" stroke-width="2"/>'
        '<path d="M6,30 L21.4,4 L98.6,4 L114,30 Z" fill="{soft}"/>',
        "diagram": '<svg viewBox="0 0 640 170" role="img" aria-label="Load test shape: ramp up, hold, ramp down">'
        '<path d="M60,130 L137.1,20 L522.9,20 L600,130" fill="none" stroke="{color}" stroke-width="2.5"/>'
        '<path d="M60,130 L137.1,20 L522.9,20 L600,130 Z" fill="{soft}" opacity="0.6"/>'
        '<line x1="60" y1="130" x2="600" y2="130" stroke="var(--border-strong)" stroke-width="1"/></svg>',
        "checks": "whether the app stays fast under the traffic volume actually expected on a normal day, held steady rather than just a quick burst.",
    },
    "stress": {
        "label": "Stress",
        "scenario": "Escalating traffic, in steps",
        "sparkline": '<path d="M6,30 L21.4,17 L52.3,17 L67.7,4 L98.6,4 L114,30" fill="none" stroke="{color}" stroke-width="2"/>'
        '<path d="M6,30 L21.4,17 L52.3,17 L67.7,4 L98.6,4 L114,30 Z" fill="{soft}"/>',
        "diagram": '<svg viewBox="0 0 640 170" role="img" aria-label="Stress test shape: step up in stages, then ramp down">'
        '<path d="M60,130 L137.1,65 L291.4,65 L368.6,20 L522.9,20 L600,130" fill="none" stroke="{color}" stroke-width="2.5"/>'
        '<path d="M60,130 L137.1,65 L291.4,65 L368.6,20 L522.9,20 L600,130 Z" fill="{soft}" opacity="0.6"/>'
        '<line x1="60" y1="130" x2="600" y2="130" stroke="var(--border-strong)" stroke-width="1"/></svg>',
        "checks": "where the app actually starts to struggle, by deliberately climbing past expected traffic in steps rather than waiting for real usage to find the ceiling.",
    },
    "spike": {
        "label": "Spike",
        "scenario": "Sudden burst, then equally sudden drop",
        "sparkline": '<path d="M6,28.3 L19,28.3 L21.1,4 L60,4 L62.2,28.3 L101,28.3 L114,30" fill="none" stroke="{color}" stroke-width="2"/>'
        '<path d="M6,28.3 L19,28.3 L21.1,4 L60,4 L62.2,28.3 L101,28.3 L114,30 Z" fill="{soft}"/>',
        "diagram": '<svg viewBox="0 0 640 170" role="img" aria-label="Spike test shape: baseline, sudden surge, hold, sudden drop, recovery">'
        '<path d="M60,121.3 L124.8,121.3 L135.6,20 L330,20 L340.8,121.3 L535.2,121.3 L600,130" fill="none" stroke="{color}" stroke-width="2.5"/>'
        '<path d="M60,121.3 L124.8,121.3 L135.6,20 L330,20 L340.8,121.3 L535.2,121.3 L600,130 Z" fill="{soft}" opacity="0.65"/>'
        '<line x1="60" y1="130" x2="600" y2="130" stroke="var(--border-strong)" stroke-width="1"/></svg>',
        "checks": "whether the app survives — and recovers from — a sudden mass-traffic surge, not just a gradual ramp.",
    },
    "soak": {
        "label": "Soak",
        "scenario": "Moderate traffic sustained for hours",
        "sparkline": '<path d="M6,30 L12.4,4 L107.6,4 L114,30" fill="none" stroke="{color}" stroke-width="2"/>'
        '<path d="M6,30 L12.4,4 L107.6,4 L114,30 Z" fill="{soft}"/>',
        "diagram": '<svg viewBox="0 0 640 170" role="img" aria-label="Soak test shape: ramp up, hold flat for a long duration, ramp down">'
        '<path d="M60,130 L91.8,20 L568.2,20 L600,130" fill="none" stroke="{color}" stroke-width="2.5"/>'
        '<path d="M60,130 L91.8,20 L568.2,20 L600,130 Z" fill="{soft}" opacity="0.6"/>'
        '<line x1="60" y1="130" x2="600" y2="130" stroke="var(--border-strong)" stroke-width="1"/></svg>',
        "checks": "whether performance holds up over time, not just at a single moment — the classic sign of a slow memory or connection leak that a short test would miss.",
    },
}

_ORDER = ["load", "stress", "spike", "soak"]
_COLOR = {"good": ("var(--good)", "var(--good-soft)"), "warn": ("var(--warn)", "var(--warn-soft)"), "bad": ("var(--bad)", "var(--bad-soft)")}


def _latest_report(test_type: str) -> Optional[Path]:
    matches = sorted(_REPORTS_DIR.glob(f"k6_{test_type}_*.json"))
    return matches[-1] if matches else None


def _metric(data: dict, name: str, key: str, default=None):
    return data.get("metrics", {}).get(name, {}).get("values", {}).get(key, default)


def _thresholds_ok(data: dict) -> bool:
    for metric in data.get("metrics", {}).values():
        for outcome in metric.get("thresholds", {}).values():
            if not outcome.get("ok", True):
                return False
    return True


def _extract(data: dict) -> Dict:
    p95_ms = _metric(data, "http_req_duration", "p(95)", 0.0)
    failed_rate = _metric(data, "http_req_failed", "rate", 0.0)
    total_requests = int(_metric(data, "http_reqs", "count", 0))
    vus_max = int(_metric(data, "vus_max", "value", 0))
    ok = _thresholds_ok(data)
    status = "good" if ok and failed_rate == 0 else ("warn" if ok else "bad")
    return {
        "p95_s": p95_ms / 1000.0,
        "failed_rate": failed_rate,
        "total_requests": total_requests,
        "vus_max": vus_max,
        "status": status,
    }


def _build_tile(test_type: str, m: Dict) -> str:
    meta = _TEST_META[test_type]
    color, soft = _COLOR[m["status"]]
    sparkline = meta["sparkline"].format(color=color, soft=soft)
    pill_label = {"good": "Pass", "warn": "Watch", "bad": "Fail"}[m["status"]]
    return f"""    <button class="tile" data-test="{test_type}" aria-expanded="false">
      <div class="row1"><span class="name">{meta['label']}</span><span class="pill {m['status']}">{pill_label}</span></div>
      <div class="scenario">{meta['scenario']}</div>
      <svg viewBox="0 0 120 36" preserveAspectRatio="none">{sparkline}</svg>
      <div class="stats">
        <div><div class="v {m['status']} mono">{m['p95_s']:.2f}s</div><div class="k">p95 resp.</div></div>
        <div><div class="v mono">{m['vus_max']}</div><div class="k">concurrent</div></div>
      </div>
      <div class="expand-cue">Details <span class="chev">&#9662;</span></div>
    </button>
"""


def _build_detail(test_type: str, m: Dict, index: int, total: int) -> Dict:
    meta = _TEST_META[test_type]
    color, soft = _COLOR[m["status"]]
    diagram = meta["diagram"].format(color=color, soft=soft)
    pass_word = {"good": "Passed", "warn": "Watch", "bad": "Failed"}[m["status"]]
    result_line = (
        f"Result: p95 response time of {m['p95_s']:.2f}s across {m['total_requests']:,} requests "
        f"at {m['vus_max']} concurrent users, with a {m['failed_rate'] * 100:.2f}% failed-request rate."
    )
    return {
        "tag": f"Test {index} of {total} · {meta['label']} · {pass_word}",
        "title": meta["label"],
        "diagram": diagram,
        "body": [
            f"What this checks: {meta['checks']}",
            f"What we ran: see k6/scripts/{test_type}-test.js for the exact stage shape and duration.",
            result_line,
        ],
    }


def _load_narrative(path: Optional[str]) -> Dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _list_items(items) -> str:
    return "\n".join(f"      <li>{i}</li>" for i in items)


def build_report(paths: Dict[str, Optional[str]], narrative: Dict, out_path: Optional[str] = None) -> Path:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    metrics_by_type: Dict[str, Dict] = {}
    for test_type in _ORDER:
        p = paths.get(test_type) or (str(_latest_report(test_type)) if _latest_report(test_type) else None)
        if not p or not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        metrics_by_type[test_type] = _extract(data)

    present = [t for t in _ORDER if t in metrics_by_type]
    tiles_html = [_build_tile(t, metrics_by_type[t]) for t in present]
    details = {
        t: _build_detail(t, metrics_by_type[t], i, len(present))
        for i, t in enumerate(present, start=1)
    }

    statuses = {metrics_by_type[t]["status"] for t in present}
    overall_status = "bad" if "bad" in statuses else ("warn" if "warn" in statuses else "good")
    verdict_icon = {"good": "✅", "warn": "⚠️", "bad": "❌"}[overall_status]

    secondary_html = ""
    if narrative.get("secondary_cards"):
        cards = []
        for card in narrative["secondary_cards"]:
            cards.append(
                f"""    <div class="card">
      <div class="row1"><span class="name">{card['name']}</span>"""
                + (f"<span class=\"pill {card.get('pill_status', 'good')}\">{card.get('pill_label', '')}</span>" if card.get("pill_label") else "")
                + f"""</div>
      <ul>
{_list_items(card['items'])}
      </ul>
    </div>"""
            )
        secondary_html = '  <div class="secondary">\n' + "\n".join(cards) + "\n  </div>"

    footnotes = narrative.get("footnotes", [])
    footnotes_html = "\n".join(f"      <span>{f}</span>" for f in footnotes)

    replacements = {
        "__TITLE__": narrative.get("title", "Performance Test Report"),
        "__EYEBROW__": narrative.get("eyebrow", "Performance Testing"),
        "__HEADLINE__": narrative.get("headline", "Results at a Glance"),
        "__PREPARED_FOR__": narrative.get("prepared_for", "the team"),
        "__PREPARED_BY__": narrative.get("prepared_by", "Rohit Mann"),
        "__ENVIRONMENT__": narrative.get("environment", "Staging"),
        "__TEST_RUN_DATE__": narrative.get("test_run_date", datetime.now().strftime("%b %d, %Y").replace(" 0", " ")),
        "__VERDICT_CLASS__": "" if overall_status == "good" else overall_status,
        "__VERDICT_ICON__": narrative.get("verdict_icon", verdict_icon),
        "__VERDICT_HEADLINE__": narrative.get("verdict_headline", "Performance run complete"),
        "__VERDICT_SUB__": narrative.get("verdict_sub", "See the tiles below for per-test results."),
        "__TILES__": "".join(tiles_html),
        "__SECONDARY_CARDS__": secondary_html,
        "__FOOTNOTES__": footnotes_html,
        "__SIGNOFF_NAME__": narrative.get("prepared_by", "Rohit Mann"),
        "__SIGNOFF_ROLE__": narrative.get("prepared_by_role", "Catalis QA"),
        "__DETAILS_JSON__": json.dumps(details),
    }

    html = template
    for token, value in replacements.items():
        html = html.replace(token, value)

    if out_path:
        out = Path(out_path)
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out = _REPORTS_DIR / f"perf_summary_{ts}.html"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--load")
    parser.add_argument("--stress")
    parser.add_argument("--spike")
    parser.add_argument("--soak")
    parser.add_argument("--narrative", help="JSON file with headline/sub/findings/recommendations/prepared_for")
    parser.add_argument("--prepared-by", help="Overrides narrative.json's prepared_by (default: Rohit Mann)")
    parser.add_argument("--prepared-by-role", help="Overrides narrative.json's prepared_by_role (default: Catalis QA)")
    parser.add_argument("--out", help="Output path (default: reports/perf_summary_<timestamp>.html)")
    args = parser.parse_args()

    narrative = _load_narrative(args.narrative)
    if args.prepared_by:
        narrative["prepared_by"] = args.prepared_by
    if args.prepared_by_role:
        narrative["prepared_by_role"] = args.prepared_by_role

    paths = {"load": args.load, "stress": args.stress, "spike": args.spike, "soak": args.soak}
    out = build_report(paths, narrative, args.out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
