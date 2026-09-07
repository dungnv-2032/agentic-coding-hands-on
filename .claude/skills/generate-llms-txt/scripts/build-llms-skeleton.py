#!/usr/bin/env python3
"""Build the SKELETON llms.txt + llms-full.txt (llmstxt.org standard) — the mechanical,
deterministic part: docs-first discovery, audience filtering, the 7-section content contract,
budget-capped self-contained rendering, the secret-scan gate, and a manifest JSON (schema 2)
for the LLM layer. Pure stdlib; discovery/audience/contract/budget/secret-scan each own their
own module — this file is orchestration only.

Output goes to STAGING files (`.llms.txt.work`, `.llms-full.txt.work`), never straight to the
final artifacts — the SKILL.md LLM step enriches + validates, then `--promote` publishes, so a
crashed run never clobbers a previously good llms.txt.

Usage:
  python3 build-llms-skeleton.py --source <repo> [--lang vi|ja|en] [--output <dir>]
                                 [--audience user|dev] [--budget <tokens>] [--index-only]
                                 [--base-url <url>] [--name <product>] [--no-interview] [--manifest -]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import audience_filter
import budget
import content_contract
import product_profile
import secret_gate
from discovery import actual_lang, openapi_specs, product_name, resolve_tier
from promote import STAGE_FULL, STAGE_SKELETON, promote
from render import full as render_full
from render import skeleton as render_skeleton

DEFAULT_BUDGET = 50000


def atomic_write(path: Path, text: str) -> None:
    """Write via a per-process temp file + os.replace so an interrupted write never leaves a
    truncated file and concurrent writers don't clobber each other's temp."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _profile_dict(profile) -> dict:
    return {"status": profile.status, "path": str(profile.path),
            "fields": dict(profile.fields), "missing_fields": list(profile.missing_fields)}


def _resolve_audience(flag: str, profile_fields: dict):
    """(audience, source) — flag > profile.audience_default > "user" default."""
    if flag:
        return flag, "flag"
    default = profile_fields.get("audience_default")
    if default in ("user", "dev"):
        return default, "profile"
    return "user", "default"


def _secret_scan_status(warnings: list) -> str:
    if not warnings:
        return "clean"
    if len(warnings) == 1 and warnings[0].startswith("secret-scan unavailable"):
        return "unavailable"
    return "warnings"


def main():
    ap = argparse.ArgumentParser(description="Build the llms.txt skeleton + manifest (deterministic)")
    ap.add_argument("--source", default=".", help="Project repo (default: cwd)")
    ap.add_argument("--lang", default="", help="Docs language (vi|ja|en) → docs/<lang> if present")
    ap.add_argument("--output", default=".", help="Directory for the final + staging files (default: cwd)")
    ap.add_argument("--base-url", default="", help="Absolute base URL for links (web-hosted llms.txt)")
    ap.add_argument("--full", action="store_true",
                    help="Deprecated no-op — llms-full.txt now stages by default; see --index-only")
    ap.add_argument("--index-only", action="store_true", help="Stage only llms.txt; skip llms-full.txt")
    ap.add_argument("--audience", default="", help="user (default) excludes build-side content; dev restores v1")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                    help=f"Token budget for llms-full.txt, estimate = chars/4 (default: {DEFAULT_BUDGET})")
    ap.add_argument("--no-interview", action="store_true",
                    help="Echoed into the manifest so the SKILL.md step can skip the profile interview")
    ap.add_argument("--require-complete", action="store_true",
                    help="CI enforcement: exit 2 when a required contract section is still a gap")
    ap.add_argument("--name", default="", help="Override the auto-detected product name")
    ap.add_argument("--manifest", default="-", help="Manifest JSON path, '-' = stdout")
    ap.add_argument("--promote", action="store_true",
                    help="Atomically publish validated staging files to final artifacts (run after enrichment)")
    args = ap.parse_args()

    if args.audience and args.audience not in ("user", "dev"):
        print(f"Error: --audience must be 'user' or 'dev', got {args.audience!r}", file=sys.stderr)
        sys.exit(1)

    if args.full:
        print("--full is deprecated: llms-full.txt now stages by default; pass --index-only to skip it.",
              file=sys.stderr)

    if args.promote:  # publish staging -> final, no discovery needed
        promote(Path(args.output).resolve(), not args.index_only)
        return

    source = Path(args.source).resolve()
    if not source.is_dir():
        print(f"Error: '{source}' is not a directory", file=sys.stderr)
        sys.exit(1)

    tier, root, files = resolve_tier(source, args.lang)
    name = args.name or product_name(source, args.lang)
    used_lang = actual_lang(source, args.lang)
    profile_dict = _profile_dict(product_profile.load(source, args.lang))
    audience, audience_source = _resolve_audience(args.audience, profile_dict["fields"])
    out = Path(args.output).resolve()

    manifest = {
        "schema": 2,
        "tier": tier,
        "audience": audience,
        "audience_source": audience_source,
        "requested_lang": args.lang or "default",
        "actual_lang": used_lang,
        "lang_fallback": bool(args.lang) and used_lang == "default",
        "product_name": name,
        "base_url": args.base_url or None,
        "openapi_count": len(openapi_specs(source)),
        "docs_root": str(root),
        "no_interview": args.no_interview,
        "profile": profile_dict,
        "final_path": str(out / "llms.txt"),
        "files": files,
    }
    if manifest["lang_fallback"]:
        manifest["warning"] = (f"Requested --lang {args.lang} but docs/{args.lang} is absent; "
                               f"content came from the default docs root. Report actual_lang, not the request.")

    if tier == 4:
        manifest["note"] = "T1-T3 empty. Needs --deep (LLM agents) or return the rebuild-spec advisory."
    else:
        out.mkdir(parents=True, exist_ok=True)
        kept, dropped, dropped_unmatched = audience_filter.apply(files, audience, profile_dict)
        sections, unclaimed = content_contract.build(kept, profile_dict, audience, dropped=dropped)
        summary = profile_dict["fields"].get("summary") if audience == "user" else None

        atomic_write(out / STAGE_SKELETON, render_skeleton(name, sections, args.base_url, summary))
        manifest["skeleton_path"] = str(out / STAGE_SKELETON)
        manifest["contract"] = [{"id": s["id"], "title": s["title"], "required": s["required"],
                                  "status": s["status"], "sources": s["sources"], "advisory": s["advisory"]}
                                 for s in sections]
        manifest["readiness"] = content_contract.readiness(sections)
        manifest["content_contract"] = {"unclaimed": [f["rel"] for f in unclaimed]}
        manifest["audience_filter"] = {"kept": len(kept), "dropped": len(dropped),
                                        "dropped_files": dropped, "dropped_unmatched": dropped_unmatched}

        if not args.index_only:
            full_text, budget_report = budget.enforce(
                sections, args.budget, lambda secs: render_full(name, secs, profile_dict, args.base_url))
            manifest["self_containment"] = budget_report.pop("self_containment")
            manifest["budget"] = budget_report
            warnings = secret_gate.scan(full_text)
            status = _secret_scan_status(warnings)
            manifest["secret_scan"] = {"status": status, "warnings": warnings,
                                        "blocks_full_artifact": status != "clean"}
            atomic_write(out / STAGE_FULL, full_text)
            manifest["full_staging_path"] = str(out / STAGE_FULL)
            manifest["final_full_path"] = str(out / "llms-full.txt")

    payload = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.manifest == "-":
        print(payload)
    else:
        Path(args.manifest).write_text(payload, encoding="utf-8")
        print(f"manifest -> {args.manifest}")

    if args.require_complete:  # emitted the manifest first, so CI can read WHAT is missing
        gaps = [s["id"] for s in manifest.get("contract", ()) if s["required"] and s["status"] == "gap"]
        if manifest["tier"] == 4:  # nothing was staged at all — incomplete by definition
            gaps.insert(0, "all (T1-T3 empty)")
        if gaps:
            print("--require-complete: required section(s) still a gap: " + ", ".join(gaps)
                  + " — see each section's advisory in the manifest.", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
