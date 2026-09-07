#!/usr/bin/env python3
"""docs/product-profile.md — the only source of product metadata a repo cannot itself carry
(name meaning, URL, owning department, person in charge, support contact, surfaces). Every
read routes through discovery.safe_read (is_file() + within() symlink containment) — never a
bare read_text on a repo path — so a profile symlinked outside the repo reads as absent, not
as content pulled from elsewhere (red-team F1). Never invents a value (FR-7): an unfilled
`<TODO ...>` placeholder parses as missing, not as content.

No wiring into the CLI pipeline here — this module is a standalone reader/writer; phase 2
imports it.
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple, Optional

from discovery import docs_root, product_name, safe_read
from md_parse import bold_fields

REQUIRED = ("name", "urls", "department", "owner", "support", "summary", "surfaces")
OPTIONAL = ("name_meaning", "audience_default")
KEYS = {
    "Product name": "name",
    "Name meaning": "name_meaning",
    "URL": "urls",
    "Department": "department",
    "Owner": "owner",
    "Support contact": "support",
    "Summary": "summary",
    "Surfaces": "surfaces",
    "Audience default": "audience_default",
}
# Vocabulary for the Surfaces field (documented for the interview + reference doc, not enforced
# here — an unrecognised surface is a human-review concern, not a parse error).
SURFACE_VOCAB = ("web", "extension", "desktop", "mobile", "cli", "api", "mcp")

_TODO_RE = re.compile(r"^<TODO\b.*>$", re.IGNORECASE)

# (bold label, internal field key, placeholder/default shown when no value is known)
TEMPLATE_FIELDS = [
    ("Product name", "name", "<TODO name>"),
    ("Name meaning", "name_meaning", "<TODO where the name comes from / what it signals>"),
    ("URL", "urls", "<TODO https://… , docs URL, download page>"),
    ("Department", "department", "<TODO owning department or team>"),
    ("Owner", "owner", "<TODO role + person in charge>"),
    ("Support contact", "support",
     "<TODO team alias or support channel — prefer a role alias over a personal address>"),
    ("Summary", "summary", "<TODO one line: what it is, who it is for, its core value>"),
    ("Surfaces", "surfaces",
     "<TODO comma list from: web, extension, desktop, mobile, cli, api, mcp>"),
    ("Audience default", "audience_default", "user"),
]


class Profile(NamedTuple):
    status: str  # "ok" | "incomplete" | "missing"
    path: Path
    fields: dict
    missing_fields: list


def _is_placeholder(value: str) -> bool:
    """Empty, or an unfilled `<TODO ...>` placeholder — both count as absent (FR-7)."""
    value = (value or "").strip()
    return not value or bool(_TODO_RE.match(value))


def _split_list(value: str) -> list:
    """Comma-split into a trimmed, non-empty list."""
    return [p.strip() for p in value.split(",") if p.strip()]


def load(source: Path, lang: str = "") -> Profile:
    """Read <docs_root>/product-profile.md through safe_read (symlink-contained; "" when
    absent OR escaping the repo — fail closed either way, red-team F1)."""
    path = docs_root(source, lang) / "product-profile.md"
    content = safe_read(path, source)
    if not content:
        return Profile(status="missing", path=path, fields={}, missing_fields=list(REQUIRED))
    raw = bold_fields(content)
    fields = {KEYS[k]: v for k, v in raw.items() if k in KEYS}
    fields = {k: v for k, v in fields.items() if not _is_placeholder(v)}  # <TODO …> == absent
    fields["urls"] = _split_list(fields.get("urls", ""))
    fields["surfaces"] = _split_list(fields.get("surfaces", ""))
    missing = [k for k in REQUIRED if not fields.get(k)]
    return Profile(status="ok" if not missing else "incomplete", path=path,
                   fields=fields, missing_fields=missing)


def per_lang_advisory(source: Path, lang: str) -> Optional[str]:
    """Advisory for a per-lang repo (docs/.rebuild-state.json declares a secondary language)
    run without --lang — docs_root() then silently resolves to the wrong root (FR-1b,
    red-team F15). The resolver itself is left alone deliberately; rewriting it is
    rebuild-spec's contract, not this skill's (YAGNI). Never raises: a malformed or unreadable
    state file yields None."""
    if lang:
        return None
    content = safe_read(source / "docs" / ".rebuild-state.json", source)
    if not content:
        return None
    try:
        state = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(state, dict):
        return None
    translations = state.get("translations")
    if not isinstance(translations, dict):
        return None
    primary = state.get("primary_lang")
    if not any(k != "primary_lang" and k != primary for k in translations):
        return None
    return ("this repo uses the per-lang docs layout; pass --lang <primary> or the profile and "
            "docs will be read from the wrong root")


def render_template(defaults: Optional[dict] = None) -> str:
    """Canonical template: `defaults` values pre-filled where known, `<TODO ...>` elsewhere.
    Single source of the file's shape — references/product-profile.md points here rather than
    restating it."""
    defaults = defaults or {}
    lines = ["---", "kind: product-profile", "owner_skill: tkm:generate-llms-txt",
              f"updated: {date.today().isoformat()}", "---", "", "# Product Profile", ""]
    for label, key, placeholder in TEMPLATE_FIELDS:
        value = defaults.get(key)
        if isinstance(value, list):
            value = ", ".join(value)
        lines.append(f"**{label}**: {value if value else placeholder}")
    return "\n".join(lines) + "\n"


def write(path: Path, fields: dict, force: bool = False) -> None:
    """Render + persist the profile atomically (pid-temp + os.replace, same style as
    build-llms-skeleton.atomic_write). Refuses to clobber an existing file unless force=True."""
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(render_template(fields), encoding="utf-8")
    os.replace(tmp, path)


def _profile_json(profile: Profile, advisory: Optional[str]) -> dict:
    payload = {"status": profile.status, "path": str(profile.path),
               "fields": dict(profile.fields), "missing_fields": list(profile.missing_fields)}
    if advisory:
        payload["advisory"] = advisory
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Read or scaffold docs/product-profile.md")
    ap.add_argument("--source", default=".", help="Project repo (default: cwd)")
    ap.add_argument("--lang", default="", help="Docs language (vi|ja|en) -> docs/<lang> if present")
    ap.add_argument("--init", action="store_true", help="Write the profile template")
    ap.add_argument("--force", action="store_true", help="Allow --init to overwrite an existing file")
    ap.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = ap.parse_args()

    source = Path(args.source).resolve()
    if not source.is_dir():
        print(f"Error: '{source}' is not a directory", file=sys.stderr)
        return 1

    advisory = per_lang_advisory(source, args.lang)

    if args.init:
        path = docs_root(source, args.lang) / "product-profile.md"
        try:
            write(path, {"name": product_name(source, args.lang)}, force=args.force)
        except FileExistsError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {path}")
        if advisory:
            print(f"advisory: {advisory}", file=sys.stderr)
        return 0

    profile = load(source, args.lang)
    if args.json:
        print(json.dumps(_profile_json(profile, advisory), ensure_ascii=False, indent=2))
    else:
        print(f"status: {profile.status}  missing_fields: {profile.missing_fields}")
        if advisory:
            print(f"advisory: {advisory}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
