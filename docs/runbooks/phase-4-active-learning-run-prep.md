# Phase 4 Active Learning Run Prep

Status: preparation checkpoint for a larger Phase 4 implementation run.

## Entry criteria

Start Phase 4 only after the Phase 2/3 local console + controlled-pilot checkpoint is committed and the repo is clean.

Required checks from repo root:

```bash
python3 -m pytest tests/test_console_api.py tests/test_server.py -q
python3 -m pytest -q
```

Required checks from `apps/console`:

```bash
npm run build
npm audit --omit=dev
```

Final hygiene check from repo root:

```bash
git diff --check
git status --short --branch
```

## Scope boundary

Phase 4 makes ShyftR visibly self-learning, but it must remain review-gated active learning rather than autonomous self-modification.

Canonical boundaries:

- Cell ledgers remain canonical truth.
- Sweep, Challenger, API, UI, and Grid surfaces are projections or delegated append-only writes.
- No second active-learning state store.
- No silent confidence, retrieval, lifecycle, isolation, deprecation, deletion, or overwrite changes.
- Proposals require review before authority changes.

## Recommended larger-run sequencing

Use `phased-assembly` with `twin-inspection` overlay. The main plan now contains explicit `/goal` gates for every tranche from 4.1 through the Phase 5 durability checkpoint; treat `docs/plans/2026-04-24-shyftr-implementation-tranches.md` as the source of truth.

Next major checkpoint: **Phase 5 durability checkpoint**. Stop there; do not begin Phase 6 without a new instruction.

Recommended autonomous sequence:

1. Phase 4.1 / Sweep Proposal Engine
   - Implement append-only proposal generation from existing Sweep reports.
   - Deduplicate against decision-folded open proposals, not raw proposal rows.
   - Add proposal fixtures before UI/API expansion.
2. Tranche 4.1G / Proposal Review Regression Gate
   - Lock accept/reject/defer/missing-rationale/duplicate-open behavior.
   - Verify proposal acceptance does not mutate Charge authority.
3. Phase 4.2 / Challenger Audit Loop
   - Start only after 4.1 and 4.1G pass full tests.
   - Challenger emits audit Sparks/proposals; it must not delete, demote, isolate, or supersede automatically.
4. Phase 4.3 / Isolation and Challenge Workflow
   - Preserve provenance.
   - Normal Packs exclude isolated guidance.
   - Audit mode can include challenged/isolated items with warnings.
5. Phase 4.4 / Memory Conflict Arbitration
   - Resolve conflicts into scoped proposals.
   - Preserve both evidence chains.
   - No silent overwrite.
6. Phase 4 Gate / Active-Learning Authority Review
   - Full Python tests, console build/audit, diff hygiene, independent reviewer PASS.
7. Phase 5.1 / Grid Metadata and Staleness
   - Grid metadata/staleness/rebuild; Grid remains non-canonical.
8. Phase 5.3 / Backup and Restore
   - Prioritize portability/recovery before heavier vector scale work.
9. Phase 5.4 / Tamper-Evident Ledger Hash Chains
   - Deterministic verification, historical tamper detection, adoption path.
10. Phase 5.5 / Privacy and Sensitivity Scoping
   - Default leakage prevention, Pack export policy, redaction projection.
11. Phase 5.2 / Disk-Backed Vector Adapter
   - Optional. Do only if dependency risk remains bounded; otherwise document deferral and close Phase 5 at durability checkpoint.
12. Phase 5 Gate / Durability Checkpoint
   - Full verification and reviewer PASS. Stop before Phase 6.

## Worker-pattern route

For the full implementation run, use persistent workers only with disjoint scopes or isolated worktrees. Keep one mutating integration owner.

Suggested lanes:

- `swarm5`: focused implementation lane for 4.1 Sweep Proposal Engine tests and backend implementation.
- `swarm10`: UI/API projection lane after backend fixture gate passes.
- `swarm6`: independent reviewer/tester across backend, UI, and doctrine boundary.
- Parent/controller: mutating integration owner and final commit authority.

If worktree isolation is not set up, use parent-session implementation plus ephemeral reviewers instead of parallel mutating persistent workers.

## Closeout requirements per tranche

Each tranche commit should report:

- files changed;
- proposal/ledger authority boundary preserved;
- tests run and exact result;
- reviewer verdict;
- remaining risks or next tranche gate.

Do not merge Phase 4.2+ changes into a 4.1 commit.
