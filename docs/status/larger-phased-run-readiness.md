# ShyftR larger phased run readiness

Status: ready-to-run packet for the next public-safe larger phased run.

Exact current start point:

- start at `Tranche 8.5: Public Alpha`;
- first wave is Wave 0 from `docs/status/tranched-plan-status.md`;
- do not advance to Checkpoint E until Tranche 8.5 evidence is recorded.

## Current evidence

| Check | Current result |
| --- | --- |
| Canonical repo clean | yes |
| Local HEAD equals origin/main | yes |
| Public readiness | PASS |
| Alpha gate | PASS locally, final verdict `ALPHA_GATE_READY` |
| Latest GitHub CI | green for current public SHA |
| Private-core repo | clean and synced |
| Public/private overlay | present in private-core docs and ignored private notes |

## Required preflight before launching workers

Run from repo root:

```bash
git fetch origin main
git status --short --branch
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
python scripts/public_readiness_check.py
bash scripts/alpha_gate.sh
HOME="$HOME" gh run list --repo stefan-mcf/shyftr --limit 3 --json headSha,status,conclusion,databaseId,name
```

Pass condition:

- clean worktree;
- exact local/remote SHA match;
- readiness PASS;
- alpha gate reaches `ALPHA_GATE_READY`;
- latest CI for the SHA is success.

## Larger run objective

Prepare and execute a controlled public-alpha evidence run that proves external technical users can install, run the gate, understand the local lifecycle, and report actionable issues.

This run is evidence collection and hardening, not a new capability sprint.

## In-scope for the larger run

- exact-SHA preflight;
- alpha tester instructions based on current public README and `docs/status/alpha-readiness.md`;
- external tester evidence collection;
- runtime-neutral replayable pilot proof if it can be done with synthetic/public-safe data;
- bug/hardening follow-up based on tester results;
- Tranche 8.5 closeout decision.

## Out of scope without a new instruction

- changing the approved public README style just to satisfy a brittle guard;
- starting Phase 6 distributed multi-cell intelligence;
- starting Phase 7 advanced/private-core differentiators in public;
- removing alpha/developer-preview posture language;
- package publication or release tags;
- hosted-service or production claims;
- real private/customer/employer/regulated data in public fixtures or reports.

## Human input gates

### Gate A: tester outreach approval

Type: escalation.

Needed before sending messages to people or posting anywhere.

The run can prepare a tester packet, but the operator decides who receives it.

### Gate B: real/pilot data approval

Type: escalation.

Needed before using anything beyond synthetic examples and operator-approved non-sensitive throwaway data.

### Gate C: Tranche 8.5 closeout

Type: escalation.

Needed before marking Tranche 8.5 complete or advancing to Checkpoint E.

## Suggested execution shape

Pattern: phased-assembly plus twin-inspection.

Use the controller as final mutating owner of the canonical repo. Use bounded helper/review lanes only when they have disjoint scope and a clear file/report contract.

Parallelizable lanes after Wave 0:

1. tester packet review lane: confirm install/gate instructions are unambiguous;
2. runtime proof lane: determine whether the public synthetic adapter examples satisfy Tranche 8.5 requirement 7 or need a follow-up;
3. status evidence lane: draft the Tranche 8.5 evidence ledger shape;
4. independent review lane: check that the run does not leak private-core details or overclaim readiness.

## Initial worker prompt skeleton

Use this for any bounded helper lane:

```text
Work in the cloned ShyftR repo root. Do not modify files unless explicitly assigned. Treat the public README as canonical public-facing wording. Keep all output public-safe: no private paths, no real data, no private-core implementation details. Current run starts at Tranche 8.5 Public Alpha. Inspect the assigned docs/code only, then produce a concise report with: PASS/BLOCKED verdict, evidence, gaps, and exact recommended next action.
```

## Closeout artifact for the run

Create/update a status note only after evidence exists:

- `docs/status/tranche-8-5-public-alpha-evidence.md`

Minimum fields:

- exact SHA;
- CI run ID;
- local alpha gate verdict;
- tester count and anonymized environment matrix;
- failures/bugs with links or summaries;
- runtime/pilot proof status;
- public/private separation review;
- final decision: keep open, close Tranche 8.5, or split follow-up.

## Current verdict

Ready to launch Wave 0 and prepare tester evidence collection.

Do not claim Tranche 8.5 complete yet.
