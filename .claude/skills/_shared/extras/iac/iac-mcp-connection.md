# AWS Pricing MCP connection

Use this reference whenever a `tkm:iac-*` skill needs AWS pricing.

## Configure

Merge [`iac-mcp-config.json`](iac-mcp-config.json) into the project's existing `.mcp.json`, or add
the same server entry to the user-level MCP settings. Do not replace an existing config file
wholesale.

Takumi does not install, merge, or update this connection. **The configured server name must be
`awslabs.aws-pricing-mcp-server`.**

No credential is required. The Price List Query API serves **public** pricing, so the server works
under whatever ambient AWS profile the MCP client was launched with — and with none at all, the
no-auth bulk Price List fallback still works.

**The profile is bound at server launch, not per tool call.** A skill cannot select an AWS profile
for a running MCP server. If a specific profile is wanted, the MCP client itself must be launched
with it. Since pricing is public and global, this almost never matters.

**Never launch the server from a skill's `Bash` tool.** It is a stdio server; the MCP client owns its
lifecycle. Shelling it out yields a process blocked on stdin and no tools — which reads as "MCP
unavailable" and silently demotes the run to the fallback path.

## Two region keys

The config pins `AWS_REGION: us-east-1`. That is `PRICING_API_REGION` — the Price List **API
endpoint**, which is not available in `ap-northeast-1`. It is **not** the region being priced, and it
is not user-overridable.

The region being priced is `DEFAULT_REGION`, read per environment from `terraform.<env>.tfvars`. See
[`layout-contract.md`](layout-contract.md).

## Version pin

`awslabs.aws-pricing-mcp-server@1.0.31`, carried over from the upstream kit for reproducibility. The
pin will age; bump it deliberately, not by accident, and re-check the tool names below when you do.

## Tools at the pinned version

`allowed-tools` is an allowlist, so an unlisted `mcp__…` tool is unavailable and the skill falls
through to the bulk path while reporting the server unreachable. The names below are read from
`@1.0.31`'s own `server.py` — re-check them whenever the pin moves.

| Tool | Granted | Why |
|---|---|---|
| `get_pricing` | yes | the core price query |
| `get_pricing_service_codes` | yes | resolve a resource's service code |
| `get_pricing_service_attributes` | yes | discover the filterable fields |
| `get_pricing_attribute_values` | yes | enumerate `usagetype` values — required for SKU precision |
| `get_price_list_urls` | yes | discover the bulk offer-file URLs for the fallback |
| `generate_cost_report` | **no** | emits its own report shape; this skill owns its formats |
| `analyze_terraform_project`, `analyze_cdk_project` | **no** | would substitute the server's own extraction for the tfvars-resolved, per-layer walk that is this skill's reason to exist |
| `get_bedrock_patterns` | **no** | unrelated |

## Availability check

Before estimating:

1. Discover the granted `mcp__awslabs.aws-pricing-mcp-server__*` tools and inspect their current
   input schemas. Confirm the schema against the live server rather than assuming it — a pin bump can
   change a field without changing a tool name.
2. If the server is absent, **say so**, then continue on the public bulk Price List and label the
   output's source as `bulk`.
3. If neither source resolves, report `CANNOT ESTIMATE`. Never substitute a remembered price.
4. Print the resolved source before estimating, and again in the output.

Do not use the AWS CLI, a deployed account, cached figures, or training-data recall to reconstruct
pricing the MCP and the bulk list could not supply.

## Related

- [`iac-mcp-config.json`](iac-mcp-config.json) — the server entry to merge
- [`layout-contract.md`](layout-contract.md) — `DEFAULT_REGION` / `PRICING_API_REGION`
- [`allowed-tools-policy.md`](allowed-tools-policy.md) — per-skill tool allowlists
