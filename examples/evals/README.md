# Synthetic eval examples

Frontier eval generation creates deterministic public-safe regression tasks from synthetic feedback and reviewed memory fixtures.

Use:

```bash
python -m shyftr.cli evalgen <cell> --output examples/evals/generated-evals.json
```

Generated tasks include:

- task id;
- provenance reference;
- expected pack item IDs;
- items to avoid;
- expected agent behavior text;
- `private_data_allowed: false`.

Do not commit real user, customer, employer, regulated, or private runtime data as eval fixtures. Public examples should use synthetic or operator-approved rows only.
