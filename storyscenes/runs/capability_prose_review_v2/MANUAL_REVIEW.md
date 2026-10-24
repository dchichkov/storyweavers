# First capability prose repair

This is an offline implementation and manual review, not another paid evaluation.
The previous Terra/Luna results and all historical data remain unchanged.
The [comparison report](REPORT.md) includes complete same-path and fresh-path
examples; both JSONL files retain every selected position, including duplicates.
The intermediate `capability_prose_review_v1` batch is also preserved.

## What changed

- A selective story view replaces repetitive custody/status paragraphs with
  the consequential actions, dialogue, ownership distinction, return duty at a
  physical pause, and actual settlement. The diagnostic view remains available.
- Dialogue uses the speaker/addressee: Vale asks for the chart "to me" and Noor
  answers "to you". Structured QA answers still identify Vale by name.
- A resolved belief names the earlier belief as well as the new one. It does
  not turn a character's mistaken expectation into a narrator's fact.
- Initial co-location supplies context without inventing motives. Stable,
  visibly supported object locations can close a story. A stale snapshot or
  partial event view cannot silently supply a final-location claim.
- New story profiles constrain the library journey to precede the return, and
  acceptance/promise to precede the observatory handoff. The new request follows
  the breached promise's assessment. These prerequisites belong to the example
  plots, not universal laws of the engine.
- QA uses visible paragraph references, including the first occurrence of a
  repeated question. Physical beats with identical question anchors cannot
  share a paragraph. Removing a statement removes its reading evidence too.

## Local results

All 30 historical trace hashes and diagnostic texts reproduce exactly. Their
paths are not repaired or reordered in the same-path comparison. All 30 matched
fresh seeds return and replay with the current story profiles, within the same
2 CPU / 6 wall second limits. These were previously successful, selected seeds;
30/30 is not a population yield estimate.

| Family | Old mean words | New mean words | Old QA count | New QA count |
| --- | ---: | ---: | ---: | ---: |
| Library | 473.0 | 243.5 | 49.5 | 19.5 |
| Harbor | 269.0 | 166.0 | 23.0 | 11.0 |
| Observatory | 155.2 | 109.0 | 10.3 | 8.4 |

QA coverage intentionally decreases because the omitted facts are no longer
visible. Neither shorter prose nor fewer questions is itself a quality gain.
All 60 resulting documents have distinct visible QA anchors; all 30 same-path
documents' exact text spans were rechecked. The complete StoryScenes suite
passes **397 tests**, including 12 new narrative regression tests. The unchanged
StoryWorlds package was not rerun in this pass. API spend: **$0**.

## Manual reading

**Library 19245:** ownership is stated once instead of repeatedly; the refusal
and its reason remain visible; the return cabinet supplies a concrete closing
location. In the old path, the return offer still precedes the trip. The fresh
profile correctly puts that interaction after the return journey. However, the
trip itself still has no enacted use for the atlas. The sequence of accepting a
request, accepting a loan and promising a return also sounds administrative.

**Harbor 19248:** repeated snapshots and audit explanations are reduced; the
reader can distinguish an old report from a fresh inspection. Yet the story
still ends with Cy accepting the old dated report, and neither that acceptance
nor Ari's inspection has a practical consequence. The numeric time references
are accurate but stiff. Harbor's plan was not changed in this pass.

**Observatory 19287:** the original path still hands over the chart before
promising it; the renderer deliberately does not hide this defect. The fresh
profile accepts, promises, delivers at time 8, misses a strict-before-8 deadline,
then refuses another job. The causal ordering is now sensible, but no enacted
obstacle explains the delay. The final object location is grounded but bland.

**Choice pinned path:** manually smoke-tested with story and QA. The competing
promises, observed priority, selected recipient, one fulfilled/one breached
promise and later refusal remain legible. The low search yield of this family
was not addressed or rebenchmarked by this prose pass.

## Next work

The remaining problem is meaningful planning: physical goals, real obstacles,
decisions and consequential outcomes. Add those to executable state and action
prerequisites, then realize them. Do not invent a motive or a clever line that
the trace cannot support. Keep distinct initial states and outcomes in the next
sample; tighter order and paragraph compaction can actually reduce measured
diversity by removing superficial permutations.

Before treating these as training stories, repeat a predeclared fresh trial,
review stories and QA together, and run blinded judging with the unchanged
rubric. The old quality and diversity scores do not apply to these revised texts.
