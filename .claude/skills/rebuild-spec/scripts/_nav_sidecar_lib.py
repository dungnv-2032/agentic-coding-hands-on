"""Reading-order JSON sidecar emitter (plan `260826-1601-package-reading-layers-index-pager`,
phase-01, rebuild-spec 28.2.0).

Serializes READING_ORDER + ROLES + QUICK_PATH + their localized prose as a
machine-readable `docs/.reading-order.json` sidecar, so the `--package` Node
bundler can consume the single source of truth instead of re-deriving its own
grouping from a hard-coded regex allowlist (see plan.md "Problem").

Presence-driven, exactly like `_nav_docmap_lib.build_document_map`: an entry
whose target is absent on disk is omitted, and its `num` is dropped from every
`roles[].nums` / `quickPath.nums`. The presence prune itself is NOT re-derived
here — it calls `_nav_aggregate_render.compute_present_nums`, the same helper
`_nav_index.build_index_readme` uses to prune the docs/README.md table, so the
two outputs are single-sourced by construction (plan phase-01, step 1).

Own module — build_navigation.py is already 240 lines; this stays out of it.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys

from _lang_lib import normalize_lang
from _nav_aggregate_render import compute_present_nums
from _nav_components_io import _atomic_write
from _nav_strings import QUICK_PATH, READING_ORDER, ROLES, get_strings
from _path_lib import _resolve_guarded

SCHEMA_VERSION = 1
SIDECAR_FILENAME = ".reading-order.json"


def _entry_payload(entry: dict, s: dict) -> dict:
    """Build one sidecar entry dict from a READING_ORDER entry + locale strings.

    Key order mirrors the plan's Architecture sample (num, kind, target, key,
    what) — cosmetic, but keeps the emitted JSON readable for the Node
    consumer that reads it next (phase-03).
    """
    descs = s["artifact_descriptions"]
    reading_why = s.get("reading_why", {})
    key = entry["key"]
    what = descs[key]
    clause = reading_why.get(key)  # layers 1-3 only; absent key -> omitted
    if clause:
        what = f"{what} — {clause}"

    payload: dict = {"num": entry["num"]}
    if "glob" in entry:
        payload["kind"] = "glob"
        payload["glob"] = entry["glob"]
        payload["link"] = entry["link"]
    else:
        payload["kind"] = "file"
        payload["path"] = entry["path"]
    payload["key"] = key
    payload["what"] = what
    return payload


def build_reading_sidecar(docs_root: str, lang: str | None) -> dict:
    """Return the sidecar payload dict (schemaVersion 1) for docs_root/lang.

    Presence-driven: an entry whose artifact is absent on disk is omitted from
    `layers[].entries` (a layer with zero surviving entries is itself omitted
    from `layers`), and its `num` is dropped from every `roles[].nums` /
    `quickPath.nums` — mirrors docs/README.md exactly via the shared
    compute_present_nums() prune, so the two can never disagree.

    Deterministic: no timestamp, no randomness, stable key/insertion order —
    two consecutive calls on an unchanged corpus return equal dicts.
    """
    s = get_strings(lang)
    nums = compute_present_nums(docs_root, READING_ORDER)

    layers = []
    for layer in READING_ORDER:
        entries = [_entry_payload(e, s) for e in layer["entries"] if e["num"] in nums]
        if not entries:
            continue
        layers.append({
            "layer": layer["layer"],
            "label": s["layer_labels"][layer["layer"]],
            "intro": s["layer_intros"][layer["layer"]],
            "entries": entries,
        })

    roles = []
    for r in ROLES:
        seq = [n for n in r["path"] if n in nums]
        if not seq:
            continue
        roles.append({
            "key": r["key"],
            "label": s["role_labels"].get(r["key"], r["key"]),
            "nums": seq,
        })

    quick_nums = [n for n in QUICK_PATH if n in nums]

    try:
        lang_code = normalize_lang(lang)
    except ValueError:
        lang_code = "en"

    return {
        "schemaVersion": SCHEMA_VERSION,
        "lang": lang_code,
        "title": s["title"],
        "quickPath": {"label": s["quick_path_label"], "nums": quick_nums},
        "roles": roles,
        "layers": layers,
        # UI chrome (Start Here / Appendix / drill labels / pager prose,
        # phase-03b) — REQUIRED, always emitted. `reading-spine.cjs`'s
        # `loadSidecar()` rejects a sidecar missing it exactly like a bad
        # `schemaVersion`; there is deliberately no English-default fallback.
        "ui": s["package_ui"],
    }


def write_reading_sidecar(docs_root: str, lang: str | None) -> None:
    """Write docs_root/.reading-order.json via the guarded atomic-write route.

    RT-F14 write-safety: resolves through `_resolve_guarded()` before writing
    and writes through `_atomic_write()` — the same route every other write in
    build_navigation.py uses. Always writes (mirrors `_write_index_readme`'s
    "always regenerated" behavior for the non-bare-root case): an empty-corpus
    docs/ still gets a sidecar, just with `"layers": []`, rather than no file
    at all — a consumer can rely on the file existing whenever the nav pass
    ran, and check `len(layers)` itself when it wants to special-case "empty".
    """
    raw = os.path.join(docs_root, SIDECAR_FILENAME)
    try:
        guarded = _resolve_guarded(raw, docs_root)
    except ValueError as e:
        print(f"[ERROR] write-safety violation for reading-order sidecar: {e}", file=sys.stderr)
        return
    payload = build_reading_sidecar(docs_root, lang)
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    try:
        _atomic_write(guarded, content)
    except OSError as e:
        print(f"[ERROR] cannot write reading-order sidecar: {e}", file=sys.stderr)
