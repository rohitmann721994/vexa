# Pulling a New Vexa Version Into an Existing Project

Every merged PR to Vexa is a version bump (`v0.3.0`, `v0.4.0`, ...) — see the
**Versioning** section in [CLAUDE.md](../CLAUDE.md). Projects created via
`bootstrap.py` reset git and point `origin` at the user's own repo, so they
have no live connection back to Vexa upstream — `git pull` won't bring in a
new version. This is the Claude Code prompt to hand a teammate whose project
was bootstrapped from an earlier Vexa clone, so they can pull in everything
released since.

Once a project has synced at least once, it also carries
`.claude/hooks/check_vexa_version.py` (a `SessionStart` hook), which checks
this automatically at the start of every Claude Code session and offers
Yes/No/Remind-later instead of the teammate having to ask for this prompt
by hand — see **Versioning** in `CLAUDE.md`. The steps below are what that
hook's "Yes" choice actually runs.

## The prompt

Paste this into Claude Code inside the teammate's project repo. Fill in
`<LATEST_VERSION>` with the tag you want them on (check
`gh release list --repo rohitmann721994/vexa` for the current one — as of
this writing it's `v0.3.0`); fill in `<FROM_VERSION>` with whatever they're
already on (check for a `.vexa-version` file in their repo root first — if
there isn't one, they're on the original `v0.1.0` baseline every bootstrap
started from).

```
Pull Vexa upstream (https://github.com/rohitmann721994/vexa) forward from <FROM_VERSION> to <LATEST_VERSION> in this project, without disturbing anything I've already customized during bootstrap.

1. Add a temporary remote: git remote add vexa-upstream https://github.com/rohitmann721994/vexa.git, then git fetch vexa-upstream --tags.
2. Run git diff <FROM_VERSION> <LATEST_VERSION> --stat (against vexa-upstream's tags) and show me the full list of files that changed between those two versions, grouped into: (a) brand-new files/folders that don't exist in my repo yet, and (b) files that already exist in my repo (these were likely customized for my project during bootstrap — project name, URLs, credentials, selectors).
3. For group (a), check out those paths directly from vexa-upstream/<LATEST_VERSION> — safe, nothing to conflict with.
4. For group (b), run git diff <FROM_VERSION> <LATEST_VERSION> -- <path> for each one and show me the diff before touching anything. Merge in only the new additions from upstream's side of the diff, keeping my project's own values (name, URLs, credentials, selectors, anything bootstrap.py wrote for me) intact everywhere else. Don't overwrite these files wholesale.
5. Check CHANGELOG.md between <FROM_VERSION> and <LATEST_VERSION> (from vexa-upstream) and summarize for me what actually changed and whether any of it needs a manual step on my end (a new tool to install, a new .env value, etc.) — call these out explicitly before we commit.
6. Write <LATEST_VERSION> to a new file .vexa-version in my project root (plain text, just the tag) so the next sync knows where to start from.
7. Stage and commit everything, then remove the vexa-upstream remote.

Confirm the plan with me — especially which group-(b) files you intend to touch and what you'll keep vs. change in each — before committing.
```

## Why this shape

- **Tags, not `main`.** `main` is a moving target; a tag is a fixed point, so
  a sync always pulls a known, released set of changes — never a
  half-merged in-progress PR.
- **`.vexa-version` marker.** Once this runs once, later syncs are
  incremental (`<FROM_VERSION>` becomes whatever the last sync landed on)
  instead of re-diffing from the original `v0.1.0` baseline every time.
- **New files vs. touched files, split explicitly.** New paths are safe to
  check out directly. Files bootstrap already customized (README, CLAUDE.md,
  `.env.example`, skill files, etc.) need a human-reviewed merge — see the
  same reasoning in `.claude/skills/setup-vexa/SKILL.md` for why bootstrap
  customization has to be respected rather than clobbered.
- **CHANGELOG called out, not silently applied.** A version bump can carry a
  manual step (installing a new binary like k6, adding an `.env` value) —
  the prompt makes Claude surface that instead of assuming a file sync alone
  is enough.
