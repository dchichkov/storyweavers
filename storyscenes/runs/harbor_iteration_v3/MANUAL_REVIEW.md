# Local-only rejected iteration

Ten stories generated, with 3 pool / 5 basin / 2 shelf endings. Not sent to judges.
The new structured measurement guards failed replay after JSON serialization:
Query.value became a dictionary instead of a typed Result. In-memory replay
passed, so the old preparation check did not catch it. The regression test did.

Preserve this batch as diagnostic evidence, not validated training material.
The next version fixes typed query decoding and checks saved-world replay during
preparation. This supports the project's physical-state north star: a narrative
decision based on measured water must remain the same decision after export.
