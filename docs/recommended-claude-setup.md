# Recommended Claude Code / AI-Assistant Setup

Vexa ships two repo-owned skills (`verify-ticket`, `write-ui-test`,
`write-api-test`) under `.claude/skills/`. Everything below is **external** —
maintained by Anthropic or third parties and installed at the user/global level,
not vendored into this repo. Install the ones your team wants so you get the
real, maintained versions instead of stale copies.

## MCP servers

| Server | Why | Install |
|--------|-----|---------|
| **Playwright MCP** | Drive the app live (headed) to explore flows and confirm selectors before writing a test — the backbone of the `verify-ticket` workflow. | Pre-wired for VS Code in `.vscode/mcp.json` (`npx @playwright/mcp@latest`, needs Node/`npx`). For other clients, add the same command to their MCP config. |

## Plugins / skills worth installing

These are not required to run the suite — they enhance how an AI assistant works
in the repo.

| Skill / plugin | Use it for |
|----------------|-----------|
| **superpowers** (brainstorming, systematic-debugging, test-driven-development, writing-plans, verification-before-completion, …) | Process discipline: design before code, debug methodically, verify before claiming done. |
| **pytest-patterns** | Idiomatic pytest — fixtures, parametrize, markers, plugins. Complements `docs/pytest-patterns.md`. |
| **accessibility-auditor** | WCAG 2.1 AA checks (axe-core + keyboard/screen-reader/focus) when your app has accessibility acceptance criteria. |
| **k6-performance** | Load testing (thresholds, scenarios, custom metrics) when a ticket needs performance verification. |

### How to install

Plugins are managed by your Claude Code installation, not this repo. Use the
plugin manager / marketplace in your Claude Code client to add them (e.g. the
official plugins marketplace for the Anthropic skills, and the superpowers
plugin from its own source). Once installed they're available in every repo you
open — including this one.

> Deliberately **not** committed here: copying these skill folders into
> `.claude/skills/` would vendor third-party, separately-licensed code that then
> drifts from upstream. Install them through the plugin manager instead.

## What ships in the repo

- `.claude/skills/verify-ticket/` — reproduce/confirm a tracker ticket → evidence
  → test → post verdict.
- `.claude/skills/write-ui-test/` — scaffold a page object + UI test.
- `.claude/skills/write-api-test/` — scaffold an authenticated API test.
- `CLAUDE.md` — project rules every assistant should read first.
