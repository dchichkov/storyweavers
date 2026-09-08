# Compact Storyscenes authoring experiment

Fresh control and compact runs use the same three theater briefs, design seeds, sample seeds, Luna authoring, Flex service and unchanged Terra set judge. Neither receives semantic critic feedback. All returned authoring tokens include reasoning and failed/repair attempts. This is a small combined-interface experiment; it does not isolate each compiler feature.

| Measure | Python control | Compact algebra |
|---|---:|---:|
| Completed worlds / attempted | 2/3 | 2/3 |
| Luna requests | 18 | 13 |
| Input tokens | 104,087 | 67,561 |
| Output tokens | 27,671 | 20,773 |
| Reasoning output tokens | 10,967 | 9,163 |
| Authoring cost estimate | $0.0284 | $0.0204 |
| Separate set-judge cost estimate | $0.0248 | $0.0270 |

Output reduction across all attempted worlds: **24.9%**. Unknown request outcomes: 0 control, 0 compact. Unknown outcomes have no measured usage and retain budget reservations.

Quality comparison covers the 2 worlds successfully judged in both runs; completion rates above remain part of the result. Scores are 0–9.

| Dimension | Control | Compact |
|---|---:|---:|
| coherence | 6.60 | 7.75 |
| style | 7.25 | 7.00 |
| grammar | 8.80 | 8.50 |
| storytelling | 6.35 | 7.80 |
| overall | 6.75 | 7.75 |
| diversity | 3.00 | 3.50 |

| Theater | Control output | Compact output | Control quality | Compact quality |
|---|---:|---:|---:|---:|
| library_parade | 9,846 | 6,310 | 7.3 | 8 |
| pond_concert | 7,617 | 6,253 | 6.2 | 7.5 |
| roof_post | 10,208 | 8,210 | unrated | unrated |

## Interrupted attempt and campaign accounting

The control reuses three completed plan responses from the interrupted compact_control_v1 attempt. They are counted once above and were not requested again. Three mechanics requests from that attempt have unrecorded paid outcomes because the disk filled; their usage is unavailable and excluded from the measured token difference. They are additional development overhead, with their full reservations retained.
The shared improvement campaign accounts for **$1.4038 of $15**, including 7 uncertain requests across this and earlier work. This is conservative local accounting, not invoice reconciliation. The exact interrupted requests and reused response hashes are saved in interrupted_control.json and the control's reused_plan_provenance.json.

The initial compact_algebra_v1 development trial accounts for **$0.0292** separately. It exposed an ending-card cross-product: incidental final facts produced 34 roof-post endings. The final implementation groups endings by declared outcomes, supplies only the intersection of facts across each group, and requests one wording per slot. The v2 benchmark starts fresh and includes all of its own repairs; its savings are not presented as a refund of this development cost.

All bounded roof-post recovery attempts are included in the compact totals above. The original draft hit its 5,500-token cap; a 575-token continuation completed its JSON without rewriting the prefix. Six subsequent small patches still did not yield a valid composition, so it remains quarantined. Completion remains 2/3; no stronger model repaired the world.

## What changed

- One executable world document replaces a prose plan followed by generated Python. Shared code supplies seeding, typed conditions/effects, knowledge slots, ownership/loan operations, wrappers and named repairs.
- Immutable kernels bind roles to physical carriers. Pattern addition pools legal opportunities; division attenuates search attention. Definitions can nest; accumulated state, guarded actions and the solver determine order. This is an operational subset of the memeplex model, not yet a universal algebra of concepts, people and whole stories.
- The library derives prose slot IDs and factual guards from executed traces. Endings share a declared outcome; their evidence contains only facts common to every represented trace. One wording per slot avoids paying for cosmetic duplicates. Luna writes wording only. Named edits require matching old text, preventing the earlier wrong-array-index failure.
- Explicit finite initial configurations are exhaustively checked; four search seeds per configuration and 100 sampled seeds build the prose inventory. This does not enumerate every reachable action ordering; unseen prose conditions fail closed.

The prior pond-concert world was separately ported without changing its behavior: 300 exact trace replays and 600 exact prose/QA replays. The old definition was 7,279 characters; the compact JSON was 4,722. These are character counts, not API token measurements.

## Limits and next gate

Three theater pairs are insufficient for a production acceptance estimate. Quality judgments have model variance. A smaller source is useful only if total authoring tokens and repair rate fall without losing story quality or causal diversity. Free English assertions still need manual semantic review; generated guard facts do not prove every sentence. Runtime remains entirely offline.

A post-benchmark guard strengthening makes closing cards check every common evidence fact, not only their outcome signature. Recompiling the saved text with those stronger guards preserved story text, trace and QA on 400 existing/fresh samples; only paragraph fact annotations changed. This is recorded in ending_guard_verification.json. The saved benchmark snapshots are unchanged.

See comparison.json for every request, stage, token count, rating and failure; see manual_review.md and verification.json for direct readings and fresh-seed validation.
