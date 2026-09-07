#!/usr/bin/env python3
"""gen-slide: render a PPTX from a project_profile.md.

Reads a profile markdown (produced by gen-md.py) and renders it into the
SVN proposal PPTX template via the role-based renderer pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Make third-party deps (python-pptx, lxml, Pillow) importable before any lib
# import. No-op on local/venv installs; self-bootstraps on the read-only,
# pip-less Claude Desktop sandbox. MUST run before importing lib.renderer.
from ensure_deps import ensure_deps
ensure_deps()

from lib.profile_parser import parse_cover_date, parse_profile
from lib.profile_schema import CoverSection, ProjectProfile
from lib.renderer import PPTXRenderer


def apply_cover_overrides(profile: ProjectProfile, company: str, date: str) -> None:
    """Force the cover's client name / date from the command line.

    The supplied-document path forbids editing the user's proposal, so when its
    addressee or date is written in a notation the parser doesn't read there is
    otherwise no way to fill the cover — the deck ships the template's
    `SVN Proposal Menu` / `2025.04.04` placeholder. These flags are that way.

    They override what the document said rather than filling only the gaps: a
    value typed on the command line is a correction, and a correction that lost
    to the document would be silently ignored. The date goes through the same
    normalizer the parser uses, so `--cover-date 2026-04-19` reaches the slide
    as `2026.04.19` like every other date.
    """
    if not (company or date):
        return
    profile.cover = CoverSection(
        company=company or profile.cover.company,
        date=(parse_cover_date(date) or date) if date else profile.cover.date,
    )
    print(f'[gen-slide] Cover overridden from the command line: '
          f'company={profile.cover.company!r} date={profile.cover.date!r}')


def main():
    ap = argparse.ArgumentParser(description='Render PPTX from project_profile markdown')
    ap.add_argument('--input', required=True, help='Path to project_content_{id}_{ts}.md')
    ap.add_argument('--output', help='Output file name without .pptx (default: derived from input)')
    ap.add_argument('--output-dir', help='Output directory (default: env SLIDE_GENERATOR__OUTPUTS_PATH or ./outputs)')
    ap.add_argument('--template', default='SVN Proposal Menu.pptx', help='Template PPTX name or path')
    ap.add_argument('--cover-company', default='',
                    help="Client company name for slide 1's headline. Overrides whatever "
                         'the document said. Use when the addressee line is written in a '
                         'notation the parser does not read.')
    ap.add_argument('--cover-date', default='',
                    help='Date for slide 1, in any notation the parser reads '
                         '(YYYY.MM.DD, YYYY/MM/DD, YYYY-MM-DD, YYYY年M月D日); anything '
                         'else is written verbatim. Overrides the document.')
    ap.add_argument('--extra-slides', help='Path to JSON file with AI-generated extra slides '
                    '(list of {title, bullets[], anchor_section|anchor_slide}). '
                    'Each slide is cloned from template slide 71 and inserted after its anchor.')
    args = ap.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        sys.exit(f'Input not found: {md_path}')

    md = md_path.read_text(encoding='utf-8')
    try:
        profile = parse_profile(md)
    except ValueError as e:
        # Raised by the front-matter `sections:` validator. A typo'd section key
        # would otherwise look exactly like a mapping that worked, so this stops
        # rather than rendering a deck the author would have to spot by eye.
        sys.exit(f'Invalid front matter in {md_path}:\n{e}')

    apply_cover_overrides(profile, args.cover_company.strip(), args.cover_date.strip())

    # Resolve template path: absolute > scripts/templates > bidding-proposal/templates
    tpl = Path(args.template)
    if not tpl.is_absolute():
        candidates = [
            Path(__file__).parent / 'templates' / args.template,
            Path(__file__).parent.parent / 'templates' / args.template,
        ]
        for c in candidates:
            if c.exists():
                tpl = c
                break
        else:
            sys.exit(f'Template not found: {args.template}')

    # Derive output name from project_id+timestamp when not given
    output_name = args.output or f'proposal_{profile.project_id}_{profile.timestamp}'

    # Auto-routed extras from unrecognized `##` headings (see profile_parser.py
    # / extra_slide_classifier.py) always apply; --extra-slides JSON (manual,
    # AI-crafted layouts) is appended on top rather than replacing them.
    extra_slides = list(profile.auto_extra_slides)
    if args.extra_slides:
        extra_path = Path(args.extra_slides)
        if not extra_path.exists():
            sys.exit(f'Extra-slides JSON not found: {extra_path}')
        try:
            manual_extra_slides = json.loads(extra_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            sys.exit(f'Invalid JSON in {extra_path}: {e}')
        if not isinstance(manual_extra_slides, list):
            sys.exit('--extra-slides JSON must be a list of slide entries')
        print(f'Loaded {len(manual_extra_slides)} extra slide(s) from {extra_path}')
        extra_slides.extend(manual_extra_slides)
    if not extra_slides:
        extra_slides = None

    renderer = PPTXRenderer()
    out_file = renderer.render_from_profile(
        profile, str(tpl), output_name, args.output_dir,
        extra_slides=extra_slides,
    )
    print(f'Done: {out_file}')
    _warn_placeholder_cover(profile)


def _warn_placeholder_cover(profile: ProjectProfile) -> None:
    """Repeat the unfilled-cover warning as the LAST thing printed.

    The parser already says it, but that line lands amid one WARNING per
    auto-routed chapter — twenty-five of them on a real proposal — where it is
    read as more of the same routine noise. Slide 1 is the first thing the
    client sees, so its placeholder gets the last word instead.
    """
    unfilled = [name for name in ('company', 'date')
                if not (getattr(profile.cover, name, '') or '').strip()]
    if not unfilled:
        return
    flags = ' '.join(f'--cover-{name} "..."' for name in unfilled)
    print(f'[gen-slide] WARNING: slide 1 still shows the TEMPLATE PLACEHOLDER — '
          f'cover {" and ".join(unfilled)} was never filled. Re-run with {flags} '
          f'before handing the deck over.')


if __name__ == '__main__':
    main()
