# ShyftR alpha readiness

Status: local-first alpha / controlled-pilot developer preview.

ShyftR is public so technical testers can clone it, run local synthetic demos, inspect the architecture, and report setup or workflow issues. It is not a hosted SaaS product, not a multi-tenant production service, and not ready for unreviewed sensitive production memory.

## Who should test now

Good alpha testers:

- developers comfortable with Python virtual environments and terminal output;
- people willing to use synthetic or non-sensitive data;
- people who can report exact commands, platform details, and error output;
- people evaluating concept clarity, install friction, CLI/demo reliability, and local console feel.

Not the right audience yet:

- non-technical users expecting a polished app;
- teams expecting hosted production service guarantees;
- anyone planning to store private/customer/regulated memory without an operator review.

## Alpha gate

After installing from the public repo, run:

```bash
bash scripts/alpha_gate.sh
```

Expected final line:

```text
ALPHA_GATE_READY
```

The gate uses synthetic data only. It checks:

- CLI import/help smoke;
- public alpha/readiness posture;
- Python tests;
- deterministic local lifecycle demo;
- synthetic replacement-readiness replay;
- diagnostic logging summary;
- optional console build and production-dependency audit when npm is available.

If the gate fails, ShyftR is not alpha-ready on that machine. Capture the full terminal output, OS, Python version, Node/npm version if relevant, and whether the failure occurred before or after dependency installation.

## Data policy for alpha testers

Use:

- synthetic examples under `examples/`;
- throwaway local Cells;
- non-sensitive notes intentionally created for testing;
- operator-approved pilot data only after reviewing `SECURITY.md`.

Do not use:

- API keys, private keys, `.env` files, or tokens;
- customer, employer, regulated, or confidential data;
- production memory ledgers;
- private operator workflows or screenshots containing secrets.

## What feedback is useful

- Did install from clone work?
- Did `scripts/alpha_gate.sh` finish with `ALPHA_GATE_READY`?
- Which README or docs step was confusing?
- Did the lifecycle demo make the Pack -> Signal loop understandable?
- Did terminology help or confuse you?
- Did the local console build or run cleanly?
- What would block you from trying a small local pilot?

## Current boundary

Alpha readiness means the local synthetic proof path is healthy enough for technical testers. It does not mean production readiness, hosted-service readiness, or broad memory-backend replacement readiness. Bounded-domain primary memory requires explicit operator approval after replay/readiness evidence and fallback/archive review.
