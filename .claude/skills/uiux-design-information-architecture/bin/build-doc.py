#!/usr/bin/env python3
"""Embed an ia-spec.json into the editor template -> a standalone, ready-to-open HTML.

The user does NOT load JSON manually: the skill runs this after generating the spec,
then hands the user the resulting .html to open directly (works offline, file://).

Usage:
  python3 bin/build-doc.py <ia-spec.json> [output.html] [--no-open]

Default output: ia-design.html next to the input JSON. Opens it in the browser
automatically unless --no-open is passed.
"""
import base64
import json
import mimetypes
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "viewer" / "ia-editor.html"
MARKER = "const EMBEDDED_SPEC = null; /*__IA_SPEC__*/"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

# --- feedback collection: ある程度使われた時点でフィードバック案内を出す ---
FEEDBACK_FORM_URL = "https://github.com/sun-asterisk-internal/takumi-design/issues"
USAGE_FILE = Path.home() / ".uiux-design-information-architecture-usage"


def feedback_nudge():
    """ビルド回数をホームの隠しファイルで数え、3回目・以降10回ごとにフィードバック案内を出力する。
    エージェントはこの [feedback] 行を見たらユーザーへリンクを提示する（SKILL.md 参照）。"""
    try:
        count = int(USAGE_FILE.read_text().strip()) if USAGE_FILE.is_file() else 0
    except (ValueError, OSError):
        count = 0
    count += 1
    try:
        USAGE_FILE.write_text(str(count))
    except OSError:
        pass  # 書き込めない環境でもビルドは止めない
    if count == 3 or (count > 3 and count % 10 == 0):
        print(f"\n[feedback] スキルを{count}回ご利用いただいています。改善のため、GitHub Issue でフィードバックをお寄せください:")
        print(f"[feedback] {FEEDBACK_FORM_URL}")
        print("[feedback] ↑ このリンクをユーザーへ提示してください。")


def to_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


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
    args = [a for a in argv[1:] if a != "--no-open"]
    no_open = "--no-open" in argv
    if not args:
        sys.exit("usage: build-doc.py <ia-spec.json> [output.html] [--no-open]")

    spec_path = Path(args[0])
    out_path = Path(args[1]) if len(args) > 1 else spec_path.with_name("ia-design.html")

    spec = json.loads(spec_path.read_text(encoding="utf-8"))  # validates JSON
    # inline any local image refs (persona portraits etc.) so the HTML stays self-contained
    embedded_imgs = embed_local_images(spec, spec_path.resolve().parent)
    if embedded_imgs:
        print(f"embedded {embedded_imgs} local image(s) as data URI")
    template = TEMPLATE.read_text(encoding="utf-8")
    if MARKER not in template:
        sys.exit(f"ERROR: embed marker not found in {TEMPLATE}")

    # </script> inside any string would break the inline <script>; escape defensively.
    embedded = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace(MARKER, f"const EMBEDDED_SPEC = {embedded}; /*__IA_SPEC__*/")

    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path}  ({len(spec.get('screens', []))} screens)")

    if not no_open:
        webbrowser.open(out_path.resolve().as_uri())  # auto-open in default browser
        print("opened in browser")

    feedback_nudge()


if __name__ == "__main__":
    main(sys.argv)
