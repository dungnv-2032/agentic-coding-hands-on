"""Tests for validate_deployment_view.py (rebuild-spec 27.13.0, phase-03).

Coverage: section-absence WARN (never FAIL), honesty label presence, the FR-5
`N/A` degradation contract (WARN + PASS), FR-7 node/edge citation presence,
the "one combined diagram, not two" merge rule (Key insight 2), diagram-type
check, secrets gate (CRITICAL — the one hard gate), CLI exit codes + summary
merge, and the two-corpus proof (with-IaC vs without-IaC).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_deployment_view import validate, main  # noqa: E402

HONESTY_LABEL = "> Derived from repository infrastructure-as-code — not verified against production."
NA_LINE = "N/A — no infrastructure-as-code found in repository."

# ---------------------------------------------------------------------------
# Fixtures — the "with-IaC" corpus: modelled on a docker-compose web app
# (nginx reverse proxy -> api -> postgres), citing a real docker-compose.yml.
# ---------------------------------------------------------------------------

WITH_IAC_ARCHITECTURE = f"""\
# Architecture

## System Architecture

```mermaid
graph TB
    A[Web Client] --> C[API Gateway]
```

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Node.js | 20 |

## Data Flow

```mermaid
sequenceDiagram
    participant UI as Client
    UI->>API: Request
```

## Deployment View

{HONESTY_LABEL}

```mermaid
flowchart TB
    subgraph AppHost
        Nginx[nginx reverse proxy]
        Api[api service]
    end
    subgraph DbHost
        Postgres[postgres]
    end
    Nginx -->|8080/http| Api
    Api -->|5432/tcp| Postgres
```

| Node / Edge | Description | Source |
|-------------|--------------|--------|
| Nginx | nginx reverse proxy service | `docker-compose.yml:3` |
| Api | api backend service | `docker-compose.yml:9` |
| Postgres | postgres database service | `docker-compose.yml:16` |
| Nginx → Api | proxy_pass upstream on 8080/http | `docker-compose.yml:6` |
| Api → Postgres | DATABASE_URL connection on 5432/tcp | `docker-compose.yml:13` |
"""

WITHOUT_IAC_ARCHITECTURE = f"""\
# Architecture

## System Architecture

```mermaid
graph TB
    A[Web Client] --> C[API Gateway]
```

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Node.js | 20 |

## Data Flow

```mermaid
sequenceDiagram
    participant UI as Client
    UI->>API: Request
```

## Deployment View

{HONESTY_LABEL}

{NA_LINE}
"""


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "architecture.md"
    p.write_text(text, encoding="utf-8")
    return p


class TestSectionAbsence:
    def test_missing_section_is_warning_never_critical(self, tmp_path):
        path = _write(tmp_path, "# Architecture\n\n## System Architecture\n\nno deployment section here\n")
        result = validate(path, tmp_path)
        assert result["status"] == "WARN"
        assert result["summary"]["critical"] == 0
        assert any(i["rule_id"] == "DeploymentView.section_missing" for i in result["issues"])

    def test_missing_file_is_warning(self, tmp_path):
        result = validate(tmp_path / "nope.md", tmp_path)
        assert result["status"] == "WARN"
        assert result["summary"]["critical"] == 0


class TestWithIaC:
    def test_clean_render_passes(self, tmp_path):
        path = _write(tmp_path, WITH_IAC_ARCHITECTURE)
        result = validate(path, tmp_path)
        assert result["summary"]["critical"] == 0
        assert not any(i["rule_id"] == "DeploymentView.label_missing" for i in result["issues"])
        assert not any(i["rule_id"] == "DeploymentView.node_uncited" for i in result["issues"])
        assert not any(i["rule_id"] == "DeploymentView.split_diagram" for i in result["issues"])

    def test_missing_honesty_label_warns(self, tmp_path):
        text = WITH_IAC_ARCHITECTURE.replace(HONESTY_LABEL + "\n\n", "")
        path = _write(tmp_path, text)
        result = validate(path, tmp_path)
        assert any(i["rule_id"] == "DeploymentView.label_missing" for i in result["issues"])
        assert result["summary"]["critical"] == 0

    def test_altered_honesty_label_warns(self, tmp_path):
        text = WITH_IAC_ARCHITECTURE.replace(HONESTY_LABEL, "> Derived from source — verified in production.")
        path = _write(tmp_path, text)
        result = validate(path, tmp_path)
        assert any(i["rule_id"] == "DeploymentView.label_missing" for i in result["issues"])

    def test_uncited_node_warns(self, tmp_path):
        """FR-7 — a node/edge with no matching `file:line` citation trips a real WARN.

        This is the negative case proving the validator CAN fail its own check
        (house failure mode guard): a diagram node with NO citation anywhere in
        the section (`Redis`, added to the flowchart but never mentioned in the
        citation table) must surface `DeploymentView.node_uncited`, not silently
        pass.
        """
        text = WITH_IAC_ARCHITECTURE.replace(
            "    Api -->|5432/tcp| Postgres\n",
            "    Api -->|5432/tcp| Postgres\n    Api -->|6379/tcp| Redis[redis cache]\n",
        )
        path = _write(tmp_path, text)
        result = validate(path, tmp_path)
        assert result["status"] == "WARN"
        uncited = [i for i in result["issues"] if i["rule_id"] == "DeploymentView.node_uncited"]
        assert any("Redis" in i["message"] for i in uncited)
        assert result["summary"]["critical"] == 0  # still WARN-first, never FAIL

    def test_split_diagram_warns(self, tmp_path):
        """Key insight 2 — infra + network must be ONE diagram, not two."""
        split = WITH_IAC_ARCHITECTURE.replace(
            "| Node / Edge | Description | Source |",
            "```mermaid\nflowchart TB\n    subgraph NetHost\n        Extra[extra net node]\n    end\n```\n\n"
            "| Node / Edge | Description | Source |",
        )
        path = _write(tmp_path, split)
        result = validate(path, tmp_path)
        assert any(i["rule_id"] == "DeploymentView.split_diagram" for i in result["issues"])

    def test_non_flowchart_diagram_type_warns(self, tmp_path):
        text = WITH_IAC_ARCHITECTURE.replace("flowchart TB", "graph TB")
        path = _write(tmp_path, text)
        result = validate(path, tmp_path)
        assert any(i["rule_id"] == "DeploymentView.diagram_type" for i in result["issues"])

    def test_secret_leak_is_critical(self, tmp_path):
        """The one hard gate — a leaked secret is critical, never warning. Every other
        defect this validator reports is recoverable by a later edit; a credential
        rendered into the docs tree is already disclosed to everyone who can read it."""
        leaked = WITH_IAC_ARCHITECTURE.replace(
            "| Postgres | postgres database service | `docker-compose.yml:16` |",
            "| Postgres | password=hunter2literal-secret-value | `docker-compose.yml:16` |",
        )
        path = _write(tmp_path, leaked)
        result = validate(path, tmp_path)
        assert result["status"] == "FAIL"
        assert result["summary"]["critical"] >= 1
        assert any(i["rule_id"] == "DeploymentView.secret_leak" for i in result["issues"])


class TestWithoutIaC:
    def test_na_degradation_warns_and_passes(self, tmp_path):
        """FR-5 — the without-IaC corpus: N/A line + WARN, run still completes (no FAIL)."""
        path = _write(tmp_path, WITHOUT_IAC_ARCHITECTURE)
        result = validate(path, tmp_path)
        assert result["status"] == "WARN"
        assert result["summary"]["critical"] == 0
        assert any(i["rule_id"] == "DeploymentView.no_iac" for i in result["issues"])

    def test_na_with_extraneous_diagram_warns(self, tmp_path):
        text = WITHOUT_IAC_ARCHITECTURE.replace(
            NA_LINE,
            NA_LINE + "\n\n```mermaid\nflowchart TB\n    subgraph X\n        Y[y]\n    end\n```\n",
        )
        path = _write(tmp_path, text)
        result = validate(path, tmp_path)
        assert any(i["rule_id"] == "DeploymentView.na_with_diagram" for i in result["issues"])


class TestArchitectureH2Order:
    """REQUIRED_H2 regression — the new section is a 4th, appended H2; the
    existing three (System Architecture, Tech Stack, Data Flow) must not move.
    """

    def test_h2_order_unchanged_plus_deployment_view(self):
        import re

        template_path = (
            Path(__file__).resolve().parent.parent.parent
            / "templates" / "architecture-template.md"
        )
        text = template_path.read_text(encoding="utf-8")
        headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
        assert headings == ["System Architecture", "Tech Stack", "Data Flow", "Deployment View"]


class TestCLI:
    def test_main_exit_zero_on_warn_only(self, tmp_path, capsys):
        artifacts = tmp_path / "plan" / "artifacts"
        artifacts.mkdir(parents=True)
        path = _write(artifacts, WITHOUT_IAC_ARCHITECTURE)
        code = main(["--architecture-file", str(path), "--project-root", str(tmp_path)])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "WARN"

    def test_main_exit_one_on_secret_leak(self, tmp_path, capsys):
        leaked = WITH_IAC_ARCHITECTURE.replace(
            "| Postgres | postgres database service | `docker-compose.yml:16` |",
            "| Postgres | password=hunter2literal-secret-value | `docker-compose.yml:16` |",
        )
        artifacts = tmp_path / "plan" / "artifacts"
        artifacts.mkdir(parents=True)
        path = _write(artifacts, leaked)
        code = main(["--architecture-file", str(path), "--project-root", str(tmp_path)])
        assert code == 1

    def test_main_plan_dir_mode_writes_summary(self, tmp_path):
        plan_dir = tmp_path / "plan"
        (plan_dir / "artifacts").mkdir(parents=True)
        (plan_dir / "artifacts" / "architecture.md").write_text(WITHOUT_IAC_ARCHITECTURE, encoding="utf-8")
        summary_path = plan_dir / "validation-summary.json"
        code = main([
            "--plan-dir", str(plan_dir),
            "--project-root", str(tmp_path),
            "--summary-out", str(summary_path),
        ])
        assert code == 0
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["validators"]["deployment_view"]["status"] == "WARN"

    def test_main_rejects_plan_dir_outside_root(self, tmp_path):
        outside = tmp_path.parent / "outside-plan"
        code = main(["--plan-dir", str(outside), "--project-root", str(tmp_path)])
        assert code == 2
