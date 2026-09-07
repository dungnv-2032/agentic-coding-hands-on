#!/usr/bin/env python3
"""Embed a um-spec.json into the viewer template -> a standalone, ready-to-open HTML.

The user does NOT load JSON manually: the skill runs this after generating the spec,
then hands the user the resulting .html to open directly (works offline, file://).

Usage:
  python3 bin/build-doc.py <um-spec.json> [output.html] [--no-open] [--annotate]

Default output: um-model.html next to the input JSON. Opens it in the browser
automatically unless --no-open is passed.

--annotate opens the page in Agentation annotation mode (appends ?annotate=1):
a visual-feedback toolbar loads (React + agentation from esm.sh) and syncs your
on-page annotations to the local Agentation MCP server (http://localhost:4747),
so the agent can read your feedback. Needs internet + the MCP server running.
"""
import base64
import json
import mimetypes
import re
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "viewer" / "um-viewer.html"
MARKER = "const EMBEDDED_SPEC = null; /*__UM_SPEC__*/"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

# --- usage-based feedback prompt -------------------------------------------
# After the skill has been used on FEEDBACK_AFTER distinct specs, print a
# one-time [feedback] line with the GitHub Issues URL. The agent (per SKILL.md) relays
# it to the user. State lives in the user's home dir; any failure is ignored —
# feedback must never break a build.
FEEDBACK_URL = "https://github.com/sun-asterisk-internal/takumi-design/issues"
FEEDBACK_AFTER = 3  # distinct um-spec.json files (rebuilds of the same spec don't count)
STATE_FILE = Path.home() / ".config" / "uiux-model-users" / "state.json"


def maybe_prompt_feedback(spec_path: Path):
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.is_file() else {}
        seen = set(state.get("specs", []))
        seen.add(str(spec_path.resolve()))
        state["specs"] = sorted(seen)
        if len(seen) >= FEEDBACK_AFTER and not state.get("feedbackShown"):
            state["feedbackShown"] = True
            print(f"[feedback] SW*-UM を{len(seen)}回ご利用いただきました。"
                  f"スキル改善のため、ぜひ GitHub Issues でフィードバックをお寄せください: {FEEDBACK_URL}")
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # never let feedback tracking break the build

# generic, reusable persona portraits shipped with the skill (p1.jpg … pN.jpg).
# A persona's `image` can reference one as "p7" / "pool:7" / "p7.jpg"; personas
# with no `image` are auto-assigned one (by order) so faces show by default.
POOL_DIR = HERE.parent / "assets" / "persona-pool"
POOL_RE = re.compile(r"^(?:pool:)?p(\d{1,2})(?:\.jpg)?$", re.IGNORECASE)


def to_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def pool_files():
    """Available pool portraits, sorted p1, p2, … pN."""
    if not POOL_DIR.is_dir():
        return []
    fs = [f for f in POOL_DIR.glob("p*.jpg") if POOL_RE.match(f.stem)]
    return sorted(fs, key=lambda f: int(POOL_RE.match(f.stem).group(1)))


def resolve_persona_pool(spec):
    """Bake the shipped persona pool into persona `image` as data URIs:
    - explicit pool ref ("p7" / "pool:7" / "p7.jpg")  → that portrait
    - no `image`                                       → auto-assign by order (faces by default)
    - data:/http/local-path `image`                    → left untouched (handled elsewhere)
    Returns count assigned."""
    pool = pool_files()
    if not pool:
        return 0
    by_stem = {f.stem.lower(): f for f in pool}
    personas = spec.get("personas") or []
    n = 0
    for i, p in enumerate(personas):
        if not isinstance(p, dict):
            continue
        img = p.get("image")
        stem = None
        if isinstance(img, str) and img.strip():
            m = POOL_RE.match(img.strip())
            if m:
                stem = "p" + m.group(1)
            else:
                continue  # explicit data:/http/local image — leave as-is
        else:
            stem = pool[i % len(pool)].stem  # auto-assign by order
        f = by_stem.get((stem or "").lower())
        if f:
            p["image"] = to_data_uri(f)
            n += 1
    return n


def embed_local_images(node, base_dir: Path):
    """Recursively replace any local image-file reference (e.g. persona `image`:
    "assets/p1.jpg") with a self-contained data URI, so the output HTML is portable.
    Already-inlined (data:) or remote (http) values are left untouched. Returns count."""
    n = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and v and not v.startswith(("data:", "http://", "https://")):
                ext = Path(v).suffix.lower()
                if (k == "image" or ext in IMG_EXTS):
                    cand = (base_dir / v) if not Path(v).is_absolute() else Path(v)
                    if cand.is_file() and cand.suffix.lower() in IMG_EXTS:
                        node[k] = to_data_uri(cand)
                        n += 1
                        continue
            n += embed_local_images(v, base_dir)
    elif isinstance(node, list):
        for item in node:
            n += embed_local_images(item, base_dir)
    return n


def main(argv):
    flags = {"--no-open", "--annotate"}
    args = [a for a in argv[1:] if a not in flags]
    no_open = "--no-open" in argv
    annotate = "--annotate" in argv
    if not args:
        sys.exit("usage: build-doc.py <um-spec.json> [output.html] [--no-open] [--annotate]")

    spec_path = Path(args[0])
    out_path = Path(args[1]) if len(args) > 1 else spec_path.with_name("um-model.html")

    spec = json.loads(spec_path.read_text(encoding="utf-8"))  # validates JSON
    # assign generic pool portraits (explicit pool refs + auto-assign for personas without an image)
    pooled = resolve_persona_pool(spec)
    if pooled:
        print(f"assigned {pooled} persona portrait(s) from the pool")
    # inline any remaining local image refs (custom portraits etc.) so the HTML stays self-contained
    embedded_imgs = embed_local_images(spec, spec_path.resolve().parent)
    if embedded_imgs:
        print(f"embedded {embedded_imgs} local image(s) as data URI")
    template = TEMPLATE.read_text(encoding="utf-8")
    if MARKER not in template:
        sys.exit(f"ERROR: embed marker not found in {TEMPLATE}")

    # </script> inside any string would break the inline <script>; escape defensively.
    embedded = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace(MARKER, f"const EMBEDDED_SPEC = {embedded}; /*__UM_SPEC__*/")

    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path}  ({len(spec.get('personas', []))} personas)")
    maybe_prompt_feedback(spec_path)

    if not no_open:
        uri = out_path.resolve().as_uri()
        if annotate:
            uri += "?annotate=1"  # load the Agentation toolbar (syncs to MCP @ :4747)
        webbrowser.open(uri)  # auto-open in default browser
        print("opened in browser" + (" (annotation mode)" if annotate else ""))
    elif annotate:
        print("note: --annotate has no effect with --no-open; open the file with ?annotate=1 to enable it")


if __name__ == "__main__":
    main(sys.argv)
