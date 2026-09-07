"""Sampled-review sizing arithmetic for the `--reviewed` delete gate (Requirement 5).

Pass A already built the MECHANICAL half of this gate: a slug-list manifest, and
`migrate_feature()` only deletes originals for a slug the manifest lists (otherwise
retained with a WARN). What was missing is the SAMPLE-SIZE arithmetic the phase file
calls for: "Sampled human review (default >=10% of features, minimum 3)" — a manifest
that lists fewer slugs than that threshold must not be honored AT ALL, even for the
slugs it does list, because a too-small sample is not a real review pass. Stdlib only.
"""
from __future__ import annotations

import math

DEFAULT_RATIO = 0.10
DEFAULT_MINIMUM = 3


def required_sample_size(total: int, *, ratio: float = DEFAULT_RATIO,
                          minimum: int = DEFAULT_MINIMUM) -> int:
    """Minimum number of reviewed features required for *total* eligible features.

    `total <= 0` -> 0 (nothing to review, nothing to gate). Otherwise the larger of
    the flat `minimum` and `ceil(total * ratio)` — a small repo still needs the
    minimum head-count, a large one needs the percentage.
    """
    if total <= 0:
        return 0
    return max(minimum, math.ceil(total * ratio))


def sample_meets_threshold(reviewed: set[str], eligible: set[str], *,
                            ratio: float = DEFAULT_RATIO,
                            minimum: int = DEFAULT_MINIMUM) -> tuple[bool, str]:
    """Whether *reviewed* (intersected with *eligible*, this run's actual candidates)
    meets the sampled-review threshold for *eligible*.

    Returns (ok, reason). `ok=False` means the WHOLE manifest must be treated as
    absent for this run — the delete step is skipped for every feature, not just the
    ones missing from the list, because the phase file frames this as a sample-size
    gate on the batch, not a per-slug allow-list check on top of an already-adequate
    sample.
    """
    required = required_sample_size(len(eligible))
    if required == 0:
        return True, "no v26 features eligible this run -- nothing to sample"
    overlap = reviewed & eligible
    if len(overlap) < required:
        return False, (
            f"--reviewed lists {len(overlap)} of {len(eligible)} eligible feature(s); "
            f"needs >= {required} (>= {DEFAULT_RATIO:.0%}, minimum {DEFAULT_MINIMUM}) "
            f"-- treating the whole manifest as absent for this run"
        )
    return True, f"--reviewed lists {len(overlap)} of {len(eligible)} eligible feature(s) (>= {required} required)"
