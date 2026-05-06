---
name: Alpha test report
about: Report a local-first ShyftR alpha gate/demo result using synthetic or approved non-sensitive data
labels: alpha-feedback
---

## Tester label

<!-- Use a public-safe handle or label. Do not include private identity details unless you want them public. -->

## Tested commit

<!-- Run: git rev-parse HEAD -->

## Environment

- OS and version:
- Python version (`python --version`):
- Node version, if console build ran (`node --version`):
- npm version, if console build ran (`npm --version`):
- Install command used:

## Alpha gate result

Command:

```bash
bash scripts/alpha_gate.sh
```

Final verdict:

<!-- Expected: ALPHA_GATE_READY -->

If the gate failed, paste the relevant synthetic/public-safe error output. Do not paste API keys, tokens, .env files, private cell ledgers, customer data, employer data, regulated data, or production memory.

## Demo/lifecycle result

- Did the deterministic lifecycle example run or make sense?
- Did the evidence -> candidate -> memory -> pack -> feedback loop make sense?
- Did the local console build/run, if tried?

## Install friction

<!-- What slowed you down or failed during clone/install/gate/demo? -->

## Concept clarity

<!-- What was clear, confusing, or misleading in README/docs? -->

## Actionable bugs or blockers

<!-- Include commands, public-safe output, and expected vs actual behavior. -->

## Data safety confirmation

- [ ] I used synthetic or intentionally non-sensitive test data only.
- [ ] I did not paste secrets, tokens, private keys, .env files, customer data, employer data, regulated data, production memory, or private operator screenshots.
