"""Behavioral tests for the `--package` diagram zoom viewer, driven in a REAL
browser (plan `260827-0811-package-html-diagram-zoom`).

Every other test for this feature in `test_build_client_package.py` is a static
assertion over the generated HTML or the viewer source. Those are cheap and they
run everywhere — but they are structurally blind to how the thing behaves, and
that blindness cost a real defect: dragging to pan from the overlay backdrop
panned the diagram AND then closed the viewer, because a press/release pair
synthesizes a trailing `click` on the nearest common ancestor no matter how far
the pointer travelled. Ten green static tests said nothing about it. This module
exists so that class of bug has somewhere to fail.

Skips (never fails) when the browser harness is absent: puppeteer ships inside
the `automate-browser` skill's own `node_modules`, which is present on a
developer machine that has run its installer and absent in a bare checkout.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/

BUILD_SCRIPT = (
    REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "scripts" / "build_client_package.cjs"
)
PUPPETEER = (
    REPO_ROOT / ".claude" / "skills" / "automate-browser" / "scripts" / "node_modules" / "puppeteer"
)

pytestmark = [
    pytest.mark.skipif(shutil.which("node") is None, reason="node not available on PATH"),
    pytest.mark.skipif(
        not PUPPETEER.is_dir(),
        reason="puppeteer not installed (run the automate-browser skill's install.sh)",
    ),
]

# A diagram deliberately WIDER than any viewport, so the overlay always has
# both diagram surface and backdrop surface to aim gestures at.
CORPUS_PAGE = textwrap.dedent(
    """\
    # Zoom Fixture

    **Project**: ZoomFixture

    ```mermaid
    flowchart LR
      A[Alpha Service] --> B[Bravo Service]
      B --> C[Charlie Service]
      C --> D[(Delta Datastore)]
      D --> E[Echo Worker]
      E --> F[Foxtrot Gateway]
    ```
    """
)


def _build(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    page = repo / "docs" / "system" / "overview.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(CORPUS_PAGE, encoding="utf-8")
    out = tmp_path / "out"
    result = subprocess.run(
        ["node", str(BUILD_SCRIPT), "--repo-root", str(repo), "--docs-root", "docs", "--out", str(out)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return out / "system" / "overview.html"


def _drive(tmp_path: Path, body: str) -> dict:
    """Run `body` inside a puppeteer page that already has the viewer loaded.

    `body` may use `p` (the page) and must assign its result to `out`.
    """
    page_url = _build(tmp_path).as_uri()
    script = tmp_path / "drive.js"
    script.write_text(
        textwrap.dedent(
            f"""\
            const puppeteer = require({json.dumps(str(PUPPETEER))});
            (async () => {{
              const b = await puppeteer.launch({{
                headless: 'new',
                args: ['--no-sandbox', '--allow-file-access-from-files'],
              }});
              const p = await b.newPage();
              const pageErrors = [];
              p.on('pageerror', (e) => pageErrors.push(String(e.message)));
              await p.setViewport({{ width: 1280, height: 800 }});
              await p.goto({json.dumps(page_url)}, {{ waitUntil: 'networkidle0' }});
              await p.waitForSelector('pre.mermaid.pkg-zoomable', {{ timeout: 20000 }});
              let out;
            {textwrap.indent(body, "  ")}
              out.pageErrors = pageErrors;
              console.log(JSON.stringify(out));
              await b.close();
            }})().catch((e) => {{ console.error(e); process.exit(1); }});
            """
        ),
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


async_open = """
  await p.evaluate(() => document.querySelector('pre.mermaid.pkg-zoomable').click());
  await p.waitForSelector('.pkg-zoom-overlay:not([hidden])', { timeout: 5000 });
"""


class TestZoomViewerBehavior:
    def test_click_opens_the_viewer_at_intrinsic_size(self, tmp_path: Path) -> None:
        """The whole point: mermaid caps the inline SVG with `max-width` so a big
        diagram is scaled DOWN to the column. The clone must escape that cap."""
        out = _drive(
            tmp_path,
            async_open
            + """
  out = await p.evaluate(() => {
    const live = document.querySelector('pre.mermaid svg');
    const clone = document.querySelector('.pkg-zoom-canvas svg');
    return {
      liveHasMaxWidthCap: live.style.maxWidth !== '',
      intrinsic: Math.round(live.viewBox.baseVal.width),
      cloneWidth: Math.round(clone.getBoundingClientRect().width),
      overlayOpen: !document.querySelector('.pkg-zoom-overlay').hidden,
    };
  });
""",
        )
        assert out["overlayOpen"]
        assert out["liveHasMaxWidthCap"], "precondition: mermaid caps the inline SVG"
        assert out["cloneWidth"] == out["intrinsic"], out

    def test_clone_keeps_its_mermaid_styling(self, tmp_path: Path) -> None:
        """REGRESSION, caught by LOOKING at a screenshot, not by a green suite:
        mermaid scopes every rule in its inline `<style>` to the SVG's own id
        (`#mermaid-1787795211799 .node rect { ... }`). Dropping that id to avoid
        a duplicate silently unstyled the whole clone — flowchart nodes lost
        their fills and rendered as solid black boxes, at every zoom level.
        """
        out = _drive(
            tmp_path,
            async_open
            + """
  out = await p.evaluate(() => {
    const live = document.querySelector('pre.mermaid svg');
    const clone = document.querySelector('.pkg-zoom-canvas svg');
    const fill = (root) => {
      const rect = root.querySelector('.node rect, .node polygon, .node path');
      return rect ? getComputedStyle(rect).fill : null;
    };
    return {
      liveFill: fill(live),
      cloneFill: fill(clone),
      idsDiffer: live.id !== clone.id && clone.id !== '',
      styleRepointed: clone.querySelector('style').textContent.indexOf('#' + live.id + ' ') === -1,
    };
  });
""",
        )
        assert out["liveFill"], "precondition: the inline diagram has a styled node"
        assert out["cloneFill"] == out["liveFill"], (
            f"clone lost its mermaid styling: {out['cloneFill']} != {out['liveFill']}"
        )
        # Styling must survive WITHOUT leaving two elements sharing one id.
        assert out["idsDiffer"], "clone reuses the original's id"
        assert out["styleRepointed"], "clone's stylesheet still points at the original id"

    def test_panning_from_the_backdrop_does_not_close_the_viewer(self, tmp_path: Path) -> None:
        """REGRESSION, found in a real Chrome run and invisible to every static
        test: a press/release pair synthesizes a trailing `click` on the nearest
        common ancestor regardless of travel, so a pan begun on the backdrop hit
        the backdrop-dismiss handler and closed the viewer it had just panned."""
        out = _drive(
            tmp_path,
            async_open
            + """
  await p.mouse.move(150, 700);
  await p.mouse.down();
  await p.mouse.move(420, 560, { steps: 8 });
  await p.mouse.up();
  await new Promise((r) => setTimeout(r, 150));
  out = await p.evaluate(() => ({
    stillOpen: !document.querySelector('.pkg-zoom-overlay').hidden,
    transform: document.querySelector('.pkg-zoom-canvas').style.transform,
  }));
""",
        )
        assert out["stillOpen"], "pan from the backdrop closed the viewer"
        assert "translate(0px, 0px)" not in out["transform"], out["transform"]

    def test_a_plain_backdrop_click_still_closes(self, tmp_path: Path) -> None:
        """Guards the fix from over-reaching: suppressing the post-pan click must
        not cost the backdrop its ordinary dismiss behavior."""
        out = _drive(
            tmp_path,
            async_open
            + """
  await p.mouse.click(150, 700);
  await new Promise((r) => setTimeout(r, 150));
  out = await p.evaluate(() => ({ closed: document.querySelector('.pkg-zoom-overlay').hidden }));
""",
        )
        assert out["closed"]

    def test_wheel_zoom_survives_a_pan(self, tmp_path: Path) -> None:
        """Wheel zoom must still work once the reader has panned — the two are
        used together constantly. An early build of this viewer got this wrong
        (wheel events resolved to the wrong element after a drag), so the
        property is asserted directly rather than left to the drag mechanism."""
        out = _drive(
            tmp_path,
            async_open
            + """
  const before = await p.evaluate(() => document.querySelector('.pkg-zoom-level').textContent);
  await p.mouse.move(640, 400);
  await p.mouse.down();
  await p.mouse.move(520, 330, { steps: 6 });
  await p.mouse.up();
  await p.mouse.move(660, 420);
  await p.mouse.wheel({ deltaY: -300 });
  await new Promise((r) => setTimeout(r, 150));
  const after = await p.evaluate(() => document.querySelector('.pkg-zoom-level').textContent);
  out = { before, after };
""",
        )
        assert out["after"] != out["before"], f"wheel zoom dead after a pan: {out}"
        assert int(out["after"].rstrip("%")) > int(out["before"].rstrip("%")), out

    def test_escape_closes_restores_focus_and_frees_the_clone(self, tmp_path: Path) -> None:
        out = _drive(
            tmp_path,
            async_open
            + """
  await p.keyboard.press('Escape');
  await new Promise((r) => setTimeout(r, 150));
  out = await p.evaluate(() => ({
    hidden: document.querySelector('.pkg-zoom-overlay').hidden,
    canvasEmptied: document.querySelector('.pkg-zoom-canvas').children.length === 0,
    focusReturned: document.activeElement.classList.contains('pkg-zoomable'),
    pageScrollRestored: getComputedStyle(document.body).overflow !== 'hidden',
    shellInteractiveAgain: document.querySelector('.pkg-shell').inert !== true,
  }));
""",
        )
        assert out["hidden"], "Escape did not close the viewer"
        assert out["canvasEmptied"], "the cloned SVG is still held after close"
        assert out["focusReturned"], "focus did not return to the diagram that opened it"
        assert out["pageScrollRestored"], "the page behind is still scroll-locked"
        assert out["shellInteractiveAgain"], "the page behind is still inert"
        assert out["pageErrors"] == [], out["pageErrors"]

    def test_page_behind_is_inert_while_open(self, tmp_path: Path) -> None:
        """`aria-modal="true"` promises assistive tech that focus stays inside
        the dialog. The shell behind is only visually covered, so without `inert`
        its sidebar links and other diagram hosts keep their place in tab order.
        """
        out = _drive(
            tmp_path,
            async_open
            + """
  out = await p.evaluate(() => ({
    shellInert: document.querySelector('.pkg-shell').inert === true,
    scrollLocked: getComputedStyle(document.body).overflow === 'hidden',
    ariaModal: document.querySelector('.pkg-zoom-overlay').getAttribute('aria-modal'),
  }));
""",
        )
        assert out["shellInert"], "page behind the modal is still tabbable"
        assert out["scrollLocked"]
        assert out["ariaModal"] == "true"

    def test_keyboard_opens_and_zooms_without_a_mouse(self, tmp_path: Path) -> None:
        out = _drive(
            tmp_path,
            """
  await p.focus('pre.mermaid.pkg-zoomable');
  await p.keyboard.press('Enter');
  await p.waitForSelector('.pkg-zoom-overlay:not([hidden])', { timeout: 5000 });
  const opened = await p.evaluate(() => document.querySelector('.pkg-zoom-level').textContent);
  await p.keyboard.press('+');
  await p.keyboard.press('+');
  await new Promise((r) => setTimeout(r, 100));
  const zoomed = await p.evaluate(() => document.querySelector('.pkg-zoom-level').textContent);
  await p.keyboard.press('1');
  await new Promise((r) => setTimeout(r, 100));
  const actual = await p.evaluate(() => document.querySelector('.pkg-zoom-level').textContent);
  out = { opened, zoomed, actual };
""",
        )
        assert int(out["zoomed"].rstrip("%")) > int(out["opened"].rstrip("%")), out
        assert out["actual"] == "100%", out

    def test_keydown_handler_is_inert_while_the_viewer_is_closed(self, tmp_path: Path) -> None:
        """The keydown listener is bound to `document` at script load, before any
        overlay exists. It must not swallow keys the page itself wants."""
        out = _drive(
            tmp_path,
            """
  out = await p.evaluate(() => {
    let defaultPrevented = null;
    document.addEventListener('keydown', (e) => { defaultPrevented = e.defaultPrevented; });
    for (const key of ['Escape', '0', '1', '+', 'ArrowDown']) {
      document.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
    }
    return {
      overlayNeverBuilt: document.querySelector('.pkg-zoom-overlay') === null,
      swallowedAKey: defaultPrevented === true,
    };
  });
""",
        )
        assert out["overlayNeverBuilt"], "the overlay must be built lazily, on first open"
        assert not out["swallowedAKey"], "the closed viewer swallowed a page keystroke"

    def test_no_console_or_page_errors_across_a_full_session(self, tmp_path: Path) -> None:
        out = _drive(
            tmp_path,
            async_open
            + """
  await p.click('[data-act="in"]');
  await p.click('[data-act="out"]');
  await p.click('[data-act="fit"]');
  await p.click('[data-act="actual"]');
  await p.mouse.move(640, 400);
  await p.mouse.down();
  await p.mouse.move(500, 500, { steps: 5 });
  await p.mouse.up();
  await p.mouse.wheel({ deltaY: -200 });
  await p.keyboard.press('Escape');
  await new Promise((r) => setTimeout(r, 150));
  out = { finished: true };
""",
        )
        assert out["pageErrors"] == [], out["pageErrors"]
