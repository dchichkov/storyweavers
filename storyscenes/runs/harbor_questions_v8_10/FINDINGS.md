# Trying before asking

## Result

The question-led script can now enact an attempt before inspecting or asking.
This changes physical history: a box can already be aboard when its contents
are discovered, a lift can fail, a crossing can be blocked, and a fastening can
open without borrowed scissors. The earlier inspect-first policy remains in
the sampler. All generation is classical execution, with no runtime LLM.

Ten fixed positions, seeds 16000-16009, were judged under the unchanged paired
Terra/Luna Flex protocol. Both judges saw the entire set, including similar
stories; each also assessed sixty uniformly selected visible QA conversations.

| Metric / 9 unless noted | Terra | Luna |
| --- | ---: | ---: |
| Storytelling | 7.2 | 7.0 |
| Overall | 7.5 | 7.6 |
| Diversity | 5 | 5 |
| Causal-path diversity | 5 | 6 |
| Language diversity | 4 | 5 |
| QA overall | 8.867 | 8.767 |
| QA usable | 58/60 | 59/60 |

This does not establish a clear overall improvement. The preceding fixed ten
scored storytelling 7.4/7.7 and diversity 4/5, on different seeds. Both current
judges recognize different sequences, but still identify the recurring harbor
task, mistaken assumption and key-return ending. Terra groups the mistaken
delivery with the two pre-delivery corrections; Luna distinguishes it. These
are genuinely different histories, not necessarily very different stories.

The failed-lift/unknown-contents case scores storytelling **6 from both**.
The simple parcel-opening case scores 6/7. A mean at seven is not evidence that
every branch clears seven. No larger paid grading follows this result.

## What changes in the world

- A local trial records a physical attempt, not a successful movement receipt.
  Load capacity is checked using the existing physical preflight; failed lifts
  grant neither custody nor completion. Successful lifts still need pickup
  and placement through the standard physical writer.
- A cup-box delivery occurs before inspection. If it is paint, Cy or Ari must
  actually remove it from the boat and put it at the sign's workbench. Correct
  cups stay aboard; hidden contents lead to actual retraction, not invented
  knowledge. Correcting the delivery does not magically supply missing cups.
- A blocked crossing requires putting the parcel back and asking for a known
  alternative. A passable crossing still requires actual travel and delivery.
- A loose fastening can open without scissors. A resisting fastening stays
  closed until the appropriate tool is handed over and the parcel is opened.
- Cy's enacted earlier promise still controls refusal and work priority. A
  later key handoff preserves the missed deadline as a breach with late repair.

These are bounded authored policies, not a general character planner. The new
local operations write only trial/resolution records; shared physical,
epistemic and social laws are unchanged. QA remains attached to visible prose
and actual event anchors. A successful attempt does not count as an inspection
of hidden contents. The change follows the physical-carrier north star by
making consequences and repair arise from actual custody, access and action.

The attempt-first flag is sampled independently at probability 0.5 after the
existing draws. The scored ten has four attempt-first stories, one per task
kind, and eight prior-promise stories. It contains no late key return, no
successful assistance after a failed lift, and no confirmation of an early
correct cup delivery. Full-grid mechanics cover these cases; this paid sample
does not certify their prose quality.

## Diversity and preservation

| v8 batch | Seed start | Exact texts | XZ / raw bytes | Paid assessment |
| --- | ---: | ---: | ---: | --- |
| 10 | 16000 | 10 | 3,748 / 14,874 (25.20%) | Above |
| 30 | 17000 | 24 | 5,736 / 43,003 (13.34%) | None |
| 100 | 63000 | 54 | 7,316 / 132,577 (5.52%) | None |

Every position replays from its serialized world. The complete declared
**256-configuration** space has **104 texts and 96 action paths**, with zero
failures. This is a doubled finite repertoire, not evidence of thousands of
semantically different stories. Both audits and all batches remain preserved.

A matched local comparison forces `attempt_first=False` on the hundred while
keeping every other condition identical. The old ordering gives 39 texts,
36 paths and 3.64% compression; the mixed ordering gives 54 texts, 52 paths
and 5.52%. Exact-paragraph repetition accounts for **90.13% versus 82.68%**
of word positions beyond each paragraph's first occurrence. The mixed corpus
has 141 exact paragraphs across 759 positions. Its shorter stories also affect
the compression ratio; neither metric is a calibrated semantic diversity score.
See the hundred's `matched_inspect_first.jsonl` and `local_review_metrics.json`.

Sources, serialized worlds, traces, all QA and judge request/response artifacts
are frozen. The v8 frozen runtime reproduces the full hundred outside the
checkout, including every story, QA set, path, plot and trace hash.

## Manual review and local correction

The better scenes have a visible cost: a wrong box must be carried back, a
blocked shortcut creates a longer delivery, and an earlier promise limits who
can help. Dialogue refers to that work. The prose nevertheless explains its
own lesson too often; adding more mechanisms has not removed the shared
"confident plan meets evidence" voice. An easy success is thin, while a failed
attempt followed only by stopping is static. Finishing Cy's independent key
delivery does not necessarily resolve Ari's dramatic problem.

Both QA judges reject `16000/c001`: the answer names Ari's belief in stone
slabs, but the opening only calls it a "stone crate." That is weaker visible
support than the answer needs. Local v9 explicitly says **Ari thought the
crate held stone slabs**. This states a belief, not the hidden contents.
Terra also rejects `c003`; that answer actually says the attempt did **not**
establish whether there were slabs. Its negation should not be read as a claim
that the contents were identified. Preserve that disagreement and all grades.

The v9 correction changes **1/2/15** story texts in the matched 10/30/100
batches. All 140 conditions, QA sets, conversations, paths, plots and trace
hashes match v8. Revised story contexts are **unjudged**; v8 scores do not
certify them. The original scored batch has not been rewritten.

The corrected v9 full-space audit again replays all 256 configurations with
104 texts and 96 paths. Its frozen runtime independently reproduces all hundred
stories, QA sets, paths, plots and trace hashes outside the checkout. The final
full StoryScenes suite passes **562 tests**, including the 128 attempt-first
cases, the original 128 cases, capacity/custody/route counterfactuals and visible
belief support. Edited Python AST, whitespace and local Markdown links check.

## Cost and next gate

All six calls returned valid results: **$0.04292835**, 26,734 input and 9,657
output tokens. Combined conservative commitment is **$4.66814665 / $5**,
leaving **$0.33185335**. Priced returned usage totals $3.06700465; the earlier
$1.601142 in uncertain reservations is unchanged. No automatic retry,
fallback tier or budget extension was used. No judge process remains active.
Coding-agent usage is separate: the checkpoint shows 31% of the weekly window
used, so no reset was needed or consumed.

The next measurable weakness is `weak_turn` after an unsuccessful or
inconclusive attempt. Test a grounded continuation that changes what a
character can do or what another character needs, rather than automatically
stopping and appending a separate fulfilled promise. Keep uncertainty honest:
new knowledge must require new access or communication. Compare matched
traces where possible, and recheck individual low-scoring stories as well as
the mean. More synonyms or a larger Boolean grid will not settle this.

The broad storytelling/diversity/replication goal remains open. This branch
does not replace the stronger default harbor baseline or justify bulk export.
