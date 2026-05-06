# Generic Worker Runtime Report evidence

Task ref: runtime-task-001
External system: generic-worker-runtime
External run: run-success-001
Kind: report

## evidence: Successful Workflow

The runtime requested a pack from ShyftR before starting a task. The pack
included a high-confidence memory about checking adapter config paths before
syncing JSONL logs. The worker applied that memory, validated the adapter
config first, then ran the task to a successful result.

Result: success
Applied memory IDs: memory-runtime-config-paths
Useful memory IDs: memory-runtime-config-paths

## evidence: Repeated Failure Signature

The same task kind previously failed three times with the same signature:

- Run 1: timeout after 30 seconds before any report was written.
- Run 2: timeout after 30 seconds with partial notes but no final report.
- Run 3: timeout after 30 seconds with the same missing-report pattern.

The repeated signature indicates an environmental limit, not a durable memory
quality issue.

## Recovery pattern

After the repeated failure signature was reviewed, the runtime increased the
timeout window from 30 seconds to 120 seconds and retried with the same pack.
Run 4 succeeded and produced this evidence plus a feedback report.

## Caution / Anti-pattern

Do not let the runtime silently mutate its own policy after one failed task.
ShyftR should export reviewable evidence and advisory proposals; the runtime
operator remains responsible for execution policy changes.
