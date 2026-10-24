# Interrupted sampler diagnostic, not the scoring baseline

No paid judge requests were sent for this run. Original attempts, frozen sources
and traces are retained as diagnostics; do not resume or use them as the primary
quality baseline.

The one-shot SIGPROF CPU timer did not reliably terminate every seed. At least
one attempt exceeded 150 CPU seconds despite the requested two-second limit.
Ordered process-pool results then stalled behind long-running seeds. The run
was interrupted, and all its worker processes exited. The reason for the missed
interrupts has not been established.

The v2 sampler uses a repeating CPU signal and a separate parent-enforced wall
timeout that kills and reaps each child. It collects completed results without
waiting for earlier seed positions. The new baseline samples fresh positions;
it does not combine these partially bounded attempts with the corrected run.
