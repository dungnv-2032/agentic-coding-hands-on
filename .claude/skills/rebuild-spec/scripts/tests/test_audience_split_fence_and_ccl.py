"""Tests for phase-04 (B4b): dev-token fencing, CCL `None.` backfill, and the
technical-spec.md provenance stamp -- see
plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/phase-04-compose-fencing-ccl-stamp.md.

`real-corpus-f001-auth/` is F001_Auth copied byte-for-byte from the real sharetribe
corpus (never invented) -- phase-01/04's measurement harness confirms its ONLY
critical rule_ids pre-fix are `FeatureSpec.ccl_blank` (4), `func.dev_token` (13), and
`func.screens_scr_unresolved` (5, P05's screen-binding job, out of scope here).
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402
from _audience_split_ccl_normalize_lib import normalize_ccl, stamp_frontmatter  # noqa: E402
from _audience_split_compose_a_lib import compose_mode_a, render_technical_spec  # noqa: E402
from _audience_split_fence_lib import FUNC_DEV_TOKEN_RE as fence_dev_token_re  # noqa: E402
from _audience_split_fence_lib import fence_dev_tokens  # noqa: E402
from _audience_split_llm_invariant_lib import check_invariants  # noqa: E402
from _audience_split_migrate_lib import validate_feature_dir  # noqa: E402
from _audience_split_parse_v26_lib import find_old_blocks  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split"
REAL_F001 = FIXTURES / "real-corpus-f001-auth"
V26_VALID = FIXTURES / "v26-valid-content"


# --------------------------------------------------------------------------- #
# fence_dev_tokens (T1-T7)
# --------------------------------------------------------------------------- #

def test_t1_fences_bare_verb_leaves_rest_verbatim():
    # Real corpus prose shape (F001_Auth functional-spec.md:16, composed output).
    line = "User submits POST /people to register"
    assert fence_dev_tokens(line) == "User submits `POST` /people to register"


def test_t2_idempotent_on_repeat_run():
    line = "User submits POST /people to register, then DELETE /sessions/:id logs out."
    once = fence_dev_tokens(line)
    twice = fence_dev_tokens(once)
    assert once == twice


def test_t3_already_fenced_token_untouched():
    line = "User submits `POST` /people to register"
    assert fence_dev_tokens(line) == line
    assert "``POST``" not in fence_dev_tokens(line)


def test_t4_file_line_shape_fenced():
    line = "see src/auth.rb:45 for detail"
    assert fence_dev_tokens(line) == "see `src/auth.rb:45` for detail"


def test_t4b_already_fenced_file_line_untouched():
    # Real dev-token fixture shape (test_validate_feature_spec.py's own regression
    # guard uses this exact bare form for src/auth.ts:42 pre-fencing).
    line = "see `src/auth.ts:42` for detail"
    assert fence_dev_tokens(line) == line


def test_t5_fenced_code_block_left_alone():
    text = "before\n```ruby\nPOST /people\n```\nafter POST /x"
    out = fence_dev_tokens(text).splitlines()
    assert out[2] == "POST /people"        # untouched inside the ``` block
    assert out[4] == "after `POST` /x"     # fenced once outside it


def test_t6_table_row_verb_fenced_cell_count_unchanged():
    # Real corpus row -- F001_Auth technical-spec.md, Artifact References table.
    row = ("| Route List | [route-list.md](../../route-list.md) | POST /people, "
           "POST /sessions, DELETE /sessions/:id, POST /sessions/request_new_password | [x] |")
    out = fence_dev_tokens(row)
    assert out.count("|") == row.count("|")
    assert out.count("`POST`") == 3
    assert "`DELETE`" in out


def test_t7_heading_line_never_modified():
    text = "## 1. Overview\n\nPOST is mentioned in prose here."
    lines = fence_dev_tokens(text).splitlines()
    assert lines[0] == "## 1. Overview"
    assert "`POST`" in lines[2]


def test_fence_pattern_is_the_validator_pattern_object():
    """DRY guard (risk table): the fence lib must import FUNC_DEV_TOKEN_RE from the
    validator, never restate the regex -- a second copy is a guaranteed future drift."""
    assert fence_dev_token_re is vfs.FUNC_DEV_TOKEN_RE


# --------------------------------------------------------------------------- #
# normalize_ccl (T8-T11)
# --------------------------------------------------------------------------- #

def test_t8_all_four_blank_ccl_sections_backfilled_in_order():
    """Real F001_Auth: Business Rules/State Machines/Algorithms/External Integrations
    each go straight from the container heading to a nested #### block with no
    intervening prose -- splicing promotes the block to H3 sibling level, which is
    exactly why the container goes blank. All four must be backfilled, in order."""
    tech_text = (REAL_F001 / "technical-spec.md").read_text(encoding="utf-8")
    out = render_technical_spec(tech_text, find_old_blocks(tech_text))

    names = ("### Business Rules", "### State Machines", "### Algorithms",
              "### External Integrations")
    positions = [out.index(name) for name in names]
    assert positions == sorted(positions), "CCL H3 order must be preserved"

    for name, pos in zip(names, positions):
        after = out[pos + len(name):]
        next_h3 = after.find("\n### ")
        body = (after[:next_h3] if next_h3 != -1 else after).strip()
        assert body == "None.", f"{name} body was {body!r}"


def test_t9_normalize_ccl_idempotent_on_already_normalized_input():
    tech_text = (REAL_F001 / "technical-spec.md").read_text(encoding="utf-8")
    out = render_technical_spec(tech_text, find_old_blocks(tech_text))
    body = out.split("\n---\n", 1)[-1] if out.startswith("---\n") else out
    lines = body.splitlines()
    once = normalize_ccl(lines)
    twice = normalize_ccl(once)
    assert once == twice


def test_t10_missing_h3_inserted_at_correct_ordinal():
    """Defensive path only -- phase-00 measured all 66 real features carry all 7
    required CCL H3s already, so this branch is unreachable on the real corpus.
    Hand-built minimal input, entirely omitting '### Algorithms'."""
    lines = [
        "# F999_Synthetic", "",
        "## Cross-Cutting Logic", "",
        "### Requirements", "", "Some requirement text.", "",
        "### Business Rules", "", "Some rule text.", "",
        "### Decision Logic", "", "Some decision text.", "",
        "### State Machines", "", "Some state text.", "",
        "### External Integrations", "", "Some integration text.", "",
        "### Verification", "", "Some verification text.", "",
        "## User Stories",
    ]
    out = normalize_ccl(lines)
    assert "### Algorithms" in out
    idx_sm = out.index("### State Machines")
    idx_alg = out.index("### Algorithms")
    idx_ext = out.index("### External Integrations")
    assert idx_sm < idx_alg < idx_ext
    body = "\n".join(out[idx_alg + 1:idx_ext]).strip()
    assert body == "None."


def test_t11_non_blank_ccl_body_untouched():
    """v26-valid-content: 'Business Rules' carries real placeholder prose before its
    BR-001 block, and 'Algorithms'/'External Integrations' are already literal
    'None.' pre-splice -- none of the three should be re-touched."""
    tech_text = (V26_VALID / "technical-spec.md").read_text(encoding="utf-8")
    out = render_technical_spec(tech_text, find_old_blocks(tech_text))
    assert "See the rule blocks below." in out
    assert out.count("### Algorithms\n\nNone.") == 1
    assert out.count("### External Integrations\n\nNone.") == 1


# --------------------------------------------------------------------------- #
# stamp_frontmatter (T12-T13)
# --------------------------------------------------------------------------- #

def test_t12_stamp_prepends_frontmatter_when_absent():
    text = "# F001_Auth\n\n## Overview\n\nBody text.\n"
    out = stamp_frontmatter(text)
    assert out.startswith("---\nauthored_by: rebuild-spec\n---\n")
    assert out[len("---\nauthored_by: rebuild-spec\n---\n"):].startswith("# F001_Auth")


def test_t13_stamp_noop_when_frontmatter_already_present():
    text = "---\nauthored_by: rebuild-spec\n---\n# F001_Auth\n\nBody.\n"
    assert stamp_frontmatter(text) == text


# --------------------------------------------------------------------------- #
# T14 -- integration on the REAL F001_Auth corpus copy
# --------------------------------------------------------------------------- #

def test_t14_integration_real_f001_auth_ccl_and_dev_token_resolved(tmp_path):
    composed = compose_mode_a(REAL_F001)
    project_root = tmp_path
    staged = project_root / "_staging" / "features" / "F001_Auth"
    staged.mkdir(parents=True)
    for name, content in composed.items():
        (staged / name).write_text(content, encoding="utf-8")

    _ok, issues = validate_feature_dir(staged, project_root)
    critical = [i for i in issues if i.get("severity") == "critical"]
    rule_ids = {i["rule_id"] for i in critical}

    assert "FeatureSpec.ccl_blank" not in rule_ids, critical
    assert "func.dev_token" not in rule_ids, critical
    # func.screens_scr_unresolved is P05's job (screen binding) -- the ONLY
    # permitted residue here.
    assert rule_ids <= {"func.screens_scr_unresolved"}, critical


# --------------------------------------------------------------------------- #
# T15 -- LLM invariant confirmation (fencing only ever ADDS a tracked token)
# --------------------------------------------------------------------------- #

def test_t15_llm_invariant_confirms_fencing_never_drops_tokens():
    pre = "User submits POST /people to register, then GET /profile shows the $10,000 balance."
    post = fence_dev_tokens(pre)
    assert pre != post
    result = check_invariants(pre, post)
    assert result.ok, result.violations
