# Luna Xhigh: Runnable Untouched, Mixed Quality

October 24, 2026. User requested xhigh after the high-reasoning follow-up.
Only `reasoning.effort` changed from high to xhigh. Same model, Flex, 64k ceiling,
frozen task/sources/schema, no failure feedback. One attempt, no retries.
This is one scenario per setting, not an estimated model-wide success rate.

## Usage And Acceptance

- Completed after **799.24 seconds (13.3 minutes)**, with a valid eight-file bundle.
- **57,503 output tokens**, including **41,292 reasoning tokens**. About 90% of
  the 64k ceiling, but status completed and no incomplete details: not truncated.
- Input 35,572 tokens, including 35,569 cache writes and zero cache reads.
- **100/100** independent seed/length positions pass exact replay, without repairs.
- Reference **835 words** fails the 900-1100 requirement; inventory mapping passes.
- Generated tests: **6/7 pass**, one scene-length assertion fails (72 > 70).
  In the 100 saved positions, two episodes exceed 70 words; overall range 44-72.
  The test's failed loop does not establish its full intended 200-position sweep.

All raw code, prose and tests remain untouched. Nothing was promoted into the
main inventory. The checker ran under the same isolated local sandbox.

## Matched Comparison

| Metric | Sol low, untouched | Luna high, repaired | Luna xhigh, untouched |
| --- | ---: | ---: | ---: |
| Runnable positions | 100/100 | 100/100 (17 before fixes) | 100/100 |
| Generated tests | 4/5 | 8/8 | 6/7 |
| Exact texts / 100 | 30 | 43 | 36 |
| Distinct paths | 6 | 15 | 6 |
| Mean story words | 352 | 430 | 403 |
| Approx. quoted-word fraction | 11.2% | 17.7% | 13.6% |
| XZ/LZMA ratio | 1.25% | 1.21% | 1.41% |
| Terra quality / 9 | 8.1 | 8.0 | 7.2 |
| Terra storytelling / 9 | 8.1 | 8.0 | 6.5 |
| Terra diversity / 9 | 2 | 1 | 3 |

High required byte-identical duplicate removal and two manual runtime fixes;
Sol and xhigh ran untouched but failed length requirements. No arm is completely
acceptance-ready. Compression is over 100 stories in checker order, not the
1,000-sample protocol, and path counts do not measure semantic diversity.

The full xhigh sample has **94 shared-grounded-kite and six shared-flight endings**.
The ten uniform judge positions (seed 777, duplicates retained) contain eight
grounded and two flights. The same positions in high contain ten flights.
Scores therefore reflect different branch mixes as well as different prose;
do not conclude that increased reasoning caused a general literary regression.
Terra rated the two flight stories 8 and the other eight stories 7, grouping
them into three plots: unsuccessful attempt, successful second flight, and snag.

[Read the ten stories](gpt-6-luna_xhigh_oneshot/quality/STORIES.md) and
[validated judge response](gpt-6-luna_xhigh_oneshot/quality/result.json).

## Manual Reading

Read all ten selected stories plus `world.py`, `prose.py` and the pack README.
The local action code is more complete: string conservation, repair consumption,
bounded planning, optional-scene effects, both roles and completed return are
explicit. The previous no-op and exact-comfort failures do not recur.
However, more state does not automatically make the prose agree with it:

- The optional marking vignette draws on the kite in the lane while its state
  still locates it at the workshop (20/100 positions). The opening only carries
  out the reel. This needs a real carrier/transfer or a different scene location.
- The failed-launch renderer always mentions a weak spar, including 70 positions
  where the inspected/repaired frame is sound. Failure can instead be caused by
  wind, tail weight or insufficient line; prose should reflect the actual cause.
- The same renderer invents a rattling gust in 12 positions with `gust=0`.
- The reel-handover action changes roles but never changes `reel.location` from
  Nia. If this field means loan custody rather than physical holder, that needs
  explicit separation; it should not silently answer holder/location QA.
- The readiness formula permits controlled flight in gusts only when June holds
  the reel, though Nia is the more experienced child. The story does not explain
  why changing who holds it is necessary for safety rather than social inclusion.
- Grounded endings are emotionally considerate but often flatten the physical
  complication into the same signed-window display. The 94% concentration makes
  the nominal parameter space much less diverse in practice.

The judge recognized the subdued payoff and repetition, but did not identify
the trace/prose mismatches above. Replay consistency is not semantic verification.
We did not repair these issues or selectively replace the judged samples.

## Cost

At published short-context [Flex rates](https://developers.openai.com/api/docs/pricing),
generation is **$0.016599-$0.018822** per attempt, about **$17-$19 per 1,000**
equivalent attempts, excluding judging/repairs. Range reflects unreported cache
write TTL. Reasoning is already included in output, not billed twice.
This is roughly 1.6-1.7x high's generation cost and 5-7x cheaper than the observed
Sol-low attempt when comparing the same cache-write durations. Not an invoice.

Conservative ledger additions are $0.0376445 generation and $0.0266775 judging.
Current accounting is **$5.52177968/$10**, including the unchanged $5 reservation
for earlier unknown Sol-agent usage. No unresolved new requests remain locally.

## Takeaway

Xhigh produced runnable code without repair, unlike high, but did not solve
length compliance, semantic continuity or branch collapse. It remains cheap;
this single result does not justify adopting it as a universal default. A few
fresh matched scenarios and explicit prose/state checks are more informative
next steps than assuming more reasoning must fix narrative quality.

Reproduction helper: `luna_xhigh_trial.py`. Six high/xhigh offline helper tests
pass, including exact request difference, frozen input hashes and preservation
of the control request. Raw response, usage, bundle, checks and judge artifacts
are in `gpt-6-luna_xhigh_oneshot/`.
