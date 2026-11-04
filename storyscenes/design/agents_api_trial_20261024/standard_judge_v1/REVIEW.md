# Sol One-Shot: Manual And Standard Judge Review

## Verdict

Promising as a way to author a small coherent story family, with validation and
targeted repair. Not evidence of a large diversity multiplier. These are the
**untouched one-shot outputs**, not a repaired pack: the hybrid workflow itself
has not been tested. No generator source was edited in this review.

The prose is appreciably better than an event log. Mara wants company rather
than applause; Ivo can decline; the dialogue creates their relationship; the
ending shows them doing something together. A failed flight is not an unfinished
story. The shared drawing is a legitimate emotional resolution.

## Method

- Existing saved pool: seeds 5000-5049 at both seven/eight-scene lengths, 100
  positions, all passing independent replay. Full-pack acceptance still fails.
- Ten positions selected uniformly without replacement using seed 777, exactly
  the earlier standard selection method. Duplicates were retained: nine exact
  texts, nine drawing endings and one flight ending. See [all ten stories](STORIES.md).
- I read all ten complete stories before reading the returned judge assessment,
  then inspected the source's state and prose branches. No numeric manual scores
  are presented as independent measurements.
- Judge: `gpt-5.6-terra`, Flex, reasoning `none`, unchanged calibration and
  story-set rubric, existing per-story plot-group response format. Only selected
  prose and calibration were sent; no code, traces, parameters or manual critique.
- Additional local diagnostic: all 24 parameter combinations at both lengths,
  fixed seed 777, run in the network-disabled sandbox. **48/48 replay passes**.
  This grid is separate from the random judge sample and is not a new IID sample.
- The original random pool covered 21 of the 24 parameter combinations. I read
  the missing useful branch with steady wind, gentle invitation, frayed line and
  no early mending, as a deliberately selected diagnostic.

## Judge Results

All scores use the standard 0-9 scale.

| Measure | Score |
| --- | ---: |
| Overall quality | 8.1 |
| Storytelling | 8.1 |
| Coherence | 8.1 |
| Style | 8.0 |
| Grammar | 9.0 |
| Overall diversity | 2 |
| Premise diversity | 1 |
| Causal-path / ending / language diversity | 2 / 2 / 2 |

Nine stories received overall 8; the successful shared-flight story received 9.
The judge found two plot groups, partitioned 9/1. It liked the concrete ending
image of Ivo pulling the second stool closer and saw most variation as minor.
Raw ratings, notes, plot assignments and usage are in [result.json](result.json).

Historical results using the same judge/rubric and ten-story sampling method:

| Pack | Authoring process | Quality | Storytelling | Diversity |
| --- | --- | ---: | ---: | ---: |
| Bakery | Supervised multi-round authoring | 7.8 | 6.8 | 2 |
| Greenhouse | Supervised multi-round authoring | 8.2 | 8.2 | 3 |
| Kite | Sol one-shot, unrepaired | 8.1 | 8.1 | 2 |

Different scenarios, small correlated samples and one judge call per pack:
this is useful context, not evidence that 8.1 is meaningfully below 8.2, or a
controlled estimate of authoring-method superiority.

## Manual Reading Notes

| Story ID | What works | Limitation or caution |
| --- | --- | --- |
| s000029 | Respects Ivo's refusal; drawing completes the social aim | Calm prevents flight, then they watch other kites without explanation |
| s000057 | Quiet shared observation and a tangible ending | Same arc as s000029 plus a removable interlude |
| s000047 | The private-field offer answers Ivo's concern | Gusts produce the same return-and-draw resolution |
| s000073 | The declined invitation is accepted without coercion | Both optional scenes add texture but not a different development |
| s000034 | Ivo's handling of the reel directly earns his final confidence | Best causal payoff here, but only one sampled flight |
| s000043 | Not pressing Ivo into helping is a real consequential choice | Early repair cannot overcome the social obstacle; still the stock drawing ending |
| s000068 | The small window/glue exchange sounds like children talking | Calm-weather ambiguity and repeated scaffold |
| s000096 | Same strengths as s000068 | Exact duplicate of s000068 despite a different generation seed |
| s000005 | The line is repaired explicitly and returned usable | Successful preparation has little payoff in the calm-weather route |
| s000085 | Deferred repair is shown, not silently applied | Taking a known unusable line out without explaining why is weakly motivated |

The targeted fray-only branch makes that last issue clearer: with a good breeze
and a willing Ivo, Mara knowingly leaves the fray, goes to the field, cannot fly,
then returns and performs the easy repair. It is mechanically consistent, but
the story needs a reason for delaying the repair. This is a motivation fix, not
an invariant fix. In contrast, abandoning flight to respect Ivo's refusal is
already motivated; it should not be treated as an error merely because flying
alone was physically possible.

I broadly agree with the judge's quality/diversity split. Its summaries are not
infallible: describing every route as a gentler invitation smooths over the
forceful-invitation branch. It also did not flag the calm-weather line or the
under-motivated deferred repair. High quality scores do not replace branch reads.

## What Needs Repair

1. **Small mechanical repair:** every `borrow` scene is only 35 or 37 words.
   The task asks for roughly 40-70, and the generated test fails even its relaxed
   38-word lower bound. This is localized prose work, not broken route planning.
   Add a useful beat rather than padding or weakening the test to manufacture a pass.
2. **Small contextual repairs:** condition the other-kites observation on weather;
   motivate why a known fray is not repaired before leaving the workshop.
3. **Composition concern:** a forced invitation leaves `ivo.trust=False` even
   after the warm drawing ending. The present story is readable, but a later
   scene composer would need an explicit representation of the newly developed
   comfort/trust instead of assuming the existing flag captures the whole arc.
4. **Larger diversity work:** change meaningful developments and responses, not
   just names, adjectives or optional inserts. Weather, trust and line condition
   currently funnel almost everything into the same ending.

The 100-position pool has 30 exact texts, six paths and 90 drawing endings.
The exhaustive grid has 42 drawing endings and six flight endings out of 48:
**87.5% grounded endings across the complete equally weighted parameter grid**.
Thus the imbalance is not just unlucky random sampling. More sampling does not
make this a broad narrative distribution. The optional vignette flags do not
affect subsequent decisions or endings; that is acceptable for atmosphere, but
they should not be counted as new causal plots.

I would test the proposed authoring workflow across multiple independent packs
and keep a modest deduplicated yield per pack. I would not estimate training-data
scale from hundreds of samples of this one generator.

## Evidence And Cost

The judge call completed on the requested model/tier with all ten valid ratings:
5,799 input tokens, 882 output tokens, zero cached/write tokens. The campaign
charged a conservative **$0.0250815 allowance**, based on published Standard
Terra rates plus an input cache-write premium, deliberately above the requested
Flex estimate. This is not an invoice. Rates were checked against the
[official model page](https://developers.openai.com/api/docs/models/gpt-5.6-terra).

Campaign accounting now totals $0.40700368 in conservative returned estimates
plus the existing unreleased $5 Sol-agent reservation, or $5.40700368 of $10.
No new agent session, generator repair, reference rewrite, QA generation or
automatic paid retry was performed.

Reproduction commands, run from the repository root (existing paid dispatches
are deliberately not repeatable):

```bash
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/judge_stories.py prepare
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/judge_stories.py judge --api-key-file .API_KEY
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/inspect_branches.py
```

Inputs, requests, source hashes, selection provenance, raw response and budget
reservation remain saved alongside this review. The branch audit contains all
48 requested results, not only the successes. Original generated files still
match the saved API bundle byte-for-byte in text content.
