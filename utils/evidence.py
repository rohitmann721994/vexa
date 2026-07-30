"""Per-step screenshot/evidence recorder for QA proof.

Each test creates an Evidence recorder, declares the scenario it verifies, and
calls `step(...)` (or `annotated_step(...)`) after every meaningful action. Every
step captures a full-page screenshot into reports/evidence/<test-name>/ and is
written to a per-scenario `steps.md`, so the screenshots, step descriptions, and
the verified acceptance criteria can be attached directly to a tracker ticket as
proof.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple

# Project-root/reports/evidence
EVIDENCE_ROOT = Path(__file__).resolve().parents[1] / "reports" / "evidence"


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return s[:60] or "step"


class Evidence:
    def __init__(self, name: str) -> None:
        self.name = name
        self.dir = EVIDENCE_ROOT / name
        self.dir.mkdir(parents=True, exist_ok=True)
        # Clear any screenshots/markdown from a previous run of this scenario.
        for old in self.dir.glob("*"):
            old.unlink()
        self.title = name
        self.description = ""
        self.criteria: List[str] = []
        self._steps: List[Tuple[int, str, str]] = []
        self._n = 0

    def scenario(self, title: str, description: str, criteria: Optional[List[str]] = None) -> None:
        """Declare the scenario under test and the acceptance criteria verified."""
        self.title = title
        self.description = description
        self.criteria = criteria or []

    def step(self, page, description: str) -> None:
        """Record a step: take a full-page screenshot and log the description."""
        self._n += 1
        filename = f"{self._n:02d}_{_slug(description)}.png"
        page.screenshot(path=str(self.dir / filename), full_page=True)
        self._steps.append((self._n, description, filename))

    def image_step(self, png_bytes: bytes, description: str) -> None:
        """Record a step from an already-rendered PNG (e.g. a downloaded
        report file rendered to an image) instead of a live page screenshot —
        for content the browser never displays on-screen."""
        self._n += 1
        filename = f"{self._n:02d}_{_slug(description)}.png"
        (self.dir / filename).write_bytes(png_bytes)
        self._steps.append((self._n, description, filename))

    _BANNER_JS = """(caption) => {
        const old = document.getElementById('__qa_evidence_banner__');
        if (old) old.remove();
        const banner = document.createElement('div');
        banner.id = '__qa_evidence_banner__';
        banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;' +
            'background:#111827;color:#fff;padding:10px 16px;font:14px/1.5 Arial,sans-serif;' +
            'box-shadow:0 2px 8px rgba(0,0,0,.6);white-space:pre-wrap;border-bottom:3px solid #ff3b30;';
        banner.textContent = caption;
        document.body.appendChild(banner);
    }"""
    _BANNER_CLEANUP_JS = """() => {
        const b = document.getElementById('__qa_evidence_banner__');
        if (b) b.remove();
    }"""
    _OUTLINE_JS = """(el) => {
        el.setAttribute('data-qa-outline', '1');
        el.style.outline = '3px solid #ff3b30';
        el.style.outlineOffset = '2px';
        el.scrollIntoView({block: 'center'});
    }"""
    _OUTLINE_CLEANUP_JS = """(el) => {
        el.style.outline = '';
        el.removeAttribute('data-qa-outline');
    }"""

    def annotated_step(self, page, description: str, expected: str = "", box_locator=None) -> None:
        """Record a step like `step()`, but overlay a caption box (step +
        expected result) and, if given, highlight the element under test with
        a red outline before capturing the screenshot.
        """
        caption = f"STEP: {description}"
        if expected:
            caption += f"\nEXPECTED: {expected}"
        page.evaluate(self._BANNER_JS, caption)
        if box_locator is not None:
            box_locator.evaluate(self._OUTLINE_JS)
        try:
            self.step(page, description)
        finally:
            page.evaluate(self._BANNER_CLEANUP_JS)
            if box_locator is not None:
                box_locator.evaluate(self._OUTLINE_CLEANUP_JS)

    def write(self) -> None:
        """Write steps.md for this scenario (embeds each screenshot in order)."""
        lines: List[str] = [f"# {self.title}", ""]
        if self.description:
            lines += [self.description, ""]
        if self.criteria:
            lines += ["**Acceptance criteria verified:**", ""]
            lines += [f"- {c}" for c in self.criteria]
            lines += [""]
        lines += ["## Steps", ""]
        for n, desc, fname in self._steps:
            lines += [f"### Step {n}: {desc}", "", f"![Step {n}]({fname})", ""]
        (self.dir / "steps.md").write_text("\n".join(lines), encoding="utf-8")
