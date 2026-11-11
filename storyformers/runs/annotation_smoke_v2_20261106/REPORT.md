# Repair-link prompt revision

Two sequential Luna/Flex requests both passed token/identity/event-reference
validation. The first wrote 5,964 shared-prefix tokens. The second reused all
5,964 cached tokens and wrote none.

Manual reading confirmed that `She`, `used`, `them` and `mend` now share `ev2`,
with `mend` the actual repair trigger. Lily, all three tools and the coat have
consistent entity references. Both reconstructed stories match the inputs.

Manual review also found a semantic defect beyond the structural validator:
the short tool-only story was labeled `obtain repair tool` despite no stated
repair purpose. This run remains saved as evidence of that over-inference.
A fifth, contrasting example was added to distinguish tool acquisition without
a purpose from explicitly established repair. See the
[final check](../annotation_smoke_v3_20261106/REPORT.md).
