# ShyftR alpha readiness

Status: local-first alpha / controlled pilot.

ShyftR is public so the operator and collaborators can clone it, run local synthetic examples, inspect the architecture, and report setup or workflow issues. It is not a hosted SaaS product, not a multi-tenant production service, and not ready for unreviewed sensitive production memory.

## Who should test now

Good alpha review scope:

- operator or collaborators comfortable with Python virtual environments and terminal output;
- synthetic or non-sensitive data only;
- exact commands, platform details, and error output recorded when relevant;
- concept clarity, install friction, CLI/example reliability, and local console feel reviewed.

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
- deterministic local lifecycle example;
- synthetic replacement-readiness replay;
- diagnostic logging summary;
- optional console build and production-dependency audit when npm is available.

If the gate fails, ShyftR is not alpha-ready on that machine. Capture the full terminal output, OS, Python version, Node/npm version if relevant, and whether the failure occurred before or after dependency installation for operator review.

## Data policy for alpha review

Use:

- synthetic examples under `examples/`;
- throwaway local cells;
- non-sensitive notes intentionally created for testing;
- operator-approved pilot data only after reviewing `SECURITY.md`.

Do not use:

- API keys, private keys, `.env` files, or tokens;
- customer, employer, regulated, or confidential data;
- production memory ledgers;
- private operator workflows or screenshots containing secrets.

## What feedback is useful

For operator review, record:

- reviewer label;
- exact commit tested from `git rev-parse HEAD`;
- OS and version;
- Python version;
- Node/npm versions if the console build runs;
- whether `scripts/alpha_gate.sh` finished with `ALPHA_GATE_READY`;
- install friction or full public-safe error output;
- whether the lifecycle demo made the pack -> feedback loop understandable;
- terminology or concept-clarity feedback;
- anything that would block a small local pilot.

## Current boundary

Alpha readiness means the local synthetic proof path is healthy enough for operator review. It does not mean production readiness, hosted-service readiness, or broad memory-backend replacement readiness. Bounded-domain primary memory requires explicit operator approval after replay/readiness evidence and fallback/archive review.
