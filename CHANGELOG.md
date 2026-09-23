# Changelog

All notable changes to Vexa are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/); versioning follows
[Semantic Versioning](https://semver.org/).

**Every merged PR is a version bump** — see the "Versioning" section in
[CLAUDE.md](CLAUDE.md) for how the bump size is decided and how the release
is cut automatically. A previous-user Claude prompt for pulling in a new
version lives in [docs/version-sync-prompt.md](docs/version-sync-prompt.md).

## [Unreleased]

## [0.3.0] - 2026-09-23
### Added
- Executive tile-grid "results at a glance" performance summary report
  (`utils/perf_summary.py`, `k6/report_template/`) — built from real k6 JSON
  metrics, with a narrative file for the human-written verdict/findings, and
  a signoff footer defaulting to `Rohit Mann` / `Catalis QA`.
- ([#1](https://github.com/rohitmann721994/vexa/pull/1))

## [0.2.0] - 2026-09-22
### Added
- `k6/` performance-testing module: smoke/load/stress/spike/soak scripts and
  a multi-endpoint scenario template, reusing `ApiLibrary`'s captured session
  cookie for auth and writing self-contained HTML+JSON reports to `reports/`.
- `.claude/skills/k6-performance/` (vendored general k6 reference) and
  `.claude/skills/write-performance-test/` (Vexa-specific scaffolding skill).
- `docs/performance-testing-guide.md`.
- `docs/templates/qa-comment-template.md` — standardized verdict-comment
  template, wired into the `verify-ticket` skill.

## [0.1.0] - 2026-08-05
### Added
- Initial framework: layered `UiLibrary`/`ApiLibrary` facades, Page Object
  Model under `pages/ui/`, evidence capture (`utils/evidence.py`), timestamped
  HTML reports, `bootstrap.py` one-command project setup, and the
  `setup-vexa` / `verify-ticket` / `write-ui-test` / `write-api-test` skills.

[Unreleased]: https://github.com/rohitmann721994/vexa/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/rohitmann721994/vexa/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rohitmann721994/vexa/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rohitmann721994/vexa/releases/tag/v0.1.0
