# IaC Idempotency Matchers

**Sole owner of the re-run guards.** Every `tkm:iac-*` generation skill resolves its idempotency
behaviour here rather than restating a matcher.

The contract these guards enforce: **re-running any generator against an existing environment is a
no-op.** `git diff` after a second run is empty. A generator never overwrites a value a human typed.

These matchers are a cross-skill lockstep anchor — upstream, `module-trainer.md` Path A step 7 uses
the same SOPS matcher as `env-composer.md` "to stay in sync". One owner is how that stays true.

## 1. tfvars create-or-append

Applies to `terraform.{env}.tfvars`.

| File state | Action |
|---|---|
| **Missing** | Create with the required blocks concatenated in order: identity → secrets/integration → (optional) route53 → tunables → hardening toggles. |
| **Exists** | **Do not overwrite.** For each required variable, test presence with the matcher below. Append only the missing ones, at the end, under a comment header naming the generator and its options. |

**Matcher — exact rule.** A variable `<varname>` is present **iff at least one non-comment line
matches**:

```
^<varname>\s*=
```

- Anchored at line start; optional whitespace before `=`.
- A line whose first non-whitespace character is `#` is a **comment** and is ignored. A fully
  commented-out assignment such as `# rds_instance_class = "db.t3.medium"` does **not** count as
  present — the variable is appended uncommented.
- Whitespace-only and blank lines are ignored.
- **Case-sensitive** — Terraform variable names are case-sensitive.

Append only the variables actually missing; skip any already present. To change a value, the user
edits the file directly — a re-run never does it for them.

**Placeholder exception on `project`.** If `terraform.{env}.tfvars` exists and `project` holds a
*real* value, it is not touched. Only a missing `project`, or one still holding a placeholder
(`project`, `<project>`, `your-project-name`), is (re)written.

## 2. SOPS secrets YAML — commented-aware matcher

Applies to `{DEPS_ROOT}/sops/secrets.{env}.yaml`.

| File state | Action |
|---|---|
| **Missing** | Create as plain YAML: header comment + the blueprint's known sensitive keys, each prefixed with the resolved `<PROJECT_PREFIX>`, every value `""`. |
| **Plain** (no trailing `sops:` metadata block) | For each blueprint key, test with the matcher below. Append only missing keys. Never touch an existing key or value. |
| **Encrypted** (has a `sops:` metadata block) | **Do not touch the file.** Print a reminder that new keys are added by opening the file through `sops`. |

**Matcher:**

```
^\s*#?\s*<KEY>\s*:
```

Anchored, case-sensitive, and **commented-aware** — it detects both the uncommented and the
commented form.

> **Why commented-aware.** A blueprint seeds some cache keys already commented out, e.g.
> `# <PROJECT>_VALKEY_PASSWORD: ""`. The simpler matcher `^<KEY>\s*:` reads those as missing and
> **re-appends them on every single run**, growing the file without bound. Fixed in PR #285; it
> supersedes PR #284's simpler matcher. Any skill that seeds SOPS keys must use the commented-aware
> form.

The generator **never decrypts** an encrypted file — it holds no KMS access — and never overwrites a
plain file's existing entries. Whitespace-only and blank lines are ignored.

Scaffolding writes a plain, unencrypted template because the generator does not hold the real secret
*values*; `sops --encrypt` would only encrypt empty strings. That plain state is working-but-unsafe
and is deliberately fail-closed: the security reviewer flags it `HIGH`, and `terraform init` errors
with a clear SOPS decryption error.

## 3. Module duplicate-scaffold guard

If the target `{MODULE_DIR}/{service}/` directory **already exists** — from a previous run, or
because a service appears in more than one layer (a shared `security-group`, for instance) — do
**not** overwrite or re-scaffold it.

Generate only the new env-folder module-call block referencing the existing local module. Multiple
env-folder blocks may legitimately share one local module source.

More generally: **never delete an existing file.** Skip generation when the file already exists.

## 4. Vendored-payload file-exists guard

The pre-committed handler payloads under `{DEPS_ROOT}/lambda-function/<name>/` are **reference-only
dependency code**. A generator references them through the `lambda` module's `code_path` /
`code_zip_path` inputs and **must not author, regenerate, or overwrite them**.

**Evaluated per file, independently.** For each of `<handler>.py` and its paired `requirements.txt`:

- File **exists** → do **not** overwrite it.
- File **absent** → **restore that one file** from source control.

Partial presence restores only the missing half — the `.py` present but `requirements.txt` absent
restores only `requirements.txt`.

**Never re-author a handler payload from prose.** These are ~1000 lines of sensitive, reviewed code;
the committed version is the canonical source. Recover it from git history or the source branch. A
prose contract is not a recovery mechanism.

### Absent and unrecoverable → hard stop

"Restore from source control" has a referent only where the payloads were committed. **This kit ships
no handler payloads**, so in a consumer repository they were never in that repo's history and there
is nothing to restore. The guard needs its third branch, or it silently falls through to the one
outcome it forbids:

- File absent **and** not in this repository's history → **stop and tell the user.** Name the file,
  say it is not recoverable here, and offer the two real options: supply the payload, or re-run with
  `alerting = false`. Do not author it, and do not proceed with a `code_path` pointing at nothing.

Proceeding is not a soft failure. `terraform validate` **passes** — `code_path` is a string, and a
string that names a missing directory is still a valid string. The environment reports as fully
wired and fails at the module's `pip install` step at apply time, long after the run that caused it.

## 5. Single continuous turn

Environment generation runs **Phase A → B → C → D sequentially, in one uninterrupted turn**, until
the environment is fully generated *and* wired. The deliverable of one invocation is a
**fully-wired** environment — never a half-built one a human has to resume.

**The mechanical rule:** accomplish every generation and wiring step with **Write, Edit and Bash
only**. Do **not** spawn, dispatch, or hand off to a sub-agent inside this flow.

The moment a child agent is dispatched, the turn ends and the pipeline stalls. There is no child to
wait on, so nothing arrives — the environment is left half-generated with un-wired cross-layer
TODOs, and the user must intervene by hand. This was the upstream bug (#367) and the tool rule is
its fix.

"Invoke the module generator for this layer" means: **execute that logic yourself, here, with your
own Write/Edit/Bash calls**, following the contracts and templates. It does not mean dispatch and
wait.

## KMS key provisioning (adjacent guard)

Not one of the five matchers, but the same idempotency class and the one with real blast radius.

Always run `describe-key alias/{sops-alias}` **first**; never create a duplicate. A duplicate KMS key
is billable and slow to delete.

Before reusing an existing key, verify it carries the `ManagedBy=aidd` tag
(`aws kms list-resource-tags --key-id <arn>`). A key without that tag is a **hard stop**, not a
warning — silently reusing a key the user does not control is worse than failing.

> **Intentional deviation from upstream.** The source warns and **still reuses**
> (`agents/env-composer.md:560`: "Still reuse (don't fail)"), and has no origin-repo conditional at
> all — it could not need one, since it only ever ran inside its own repository. This kit ships to
> arbitrary repositories, where an untagged key at that alias is far more likely to be someone
> else's. Encrypting secrets against a key the user does not control is not recoverable by a warning
> line. **Do not revert this to a warning when transcribing from the source.**
>
> The stop is unconditional. An earlier draft exempted the origin repository, which is where the
> `ORG`/`REPO` keys came from — but a conditional that only ever relaxes the guard in the one
> repository whose keys are already tagged buys nothing and gives the rule a branch to be lost
> through. `ORG`/`REPO` are provenance only; no skill reads them.

## Related contracts

- [`layout-contract.md`](./layout-contract.md) — `DEPS_ROOT`, `MODULE_DIR`, `SOPS_ALIAS_PATTERN`
- [`finding-format.md`](./finding-format.md) — reviewer finding line and parse regex
- [`allowed-tools-policy.md`](./allowed-tools-policy.md) — per-skill tool allowlists
