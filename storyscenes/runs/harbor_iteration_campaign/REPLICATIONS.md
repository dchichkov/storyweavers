# Replication notes

These are deliberately authored offline generators, not paid LLM-generated
scripts. Coding-agent author effort is not included in the judge API costs.
The question is whether readable scene-level prose can coexist with enacted
world changes, not whether this currently produces a large training corpus.

## Greenhouse

`greenhouse_story.py` extends a local capability registry with plants, finite
water and tool supplies, and timestamped inspections. Treatment requires an
inspection of the current soil state. Water is conserved between supplies,
soil, drain tray and puddle. Stakes must be long enough, consume cord and remain
physically attached. Light consumes clock time or battery charge; the sill
holds one pot. Recovery is a bounded next-morning rule, not horticultural
prediction. Ownership of the two plants is explicit.

`greenhouse_prose.py` writes scenes around diagnosis, protection, sharing light,
and a leaking can. The same drooping plant can require opposite treatments.
A missed light turn can remain unresolved. No prose model runs at sampling time.

Manual reading of all ten first samples found coherent beginnings, dialogue,
turns and concrete endings, but three support stories largely repeated the same
solution. The judges agreed on storytelling 7.8 and diversity 4. Their QA review
identified a comparison to unmentioned drainage and a question mentioning cord
where only stake length was narrated. Those two phrases were narrowed in v2.
Some Luna explanations incorrectly claimed an answer said cord was available;
it did not. Treat the diagnoses as review leads, not unquestionable truth.

The prepared v1 thirty is preserved but unjudged. V2 uses the same thirty stories
and traces, changing only those QA phrases. Fresh seeds 1000-1029 scored
storytelling 8.733/7.900 and diversity 4/3 (Terra/Luna). The set has only 19 exact
texts; all 30 positions remained in both judge requests. QA usable: 180/180 and
178/180. This is encouraging prose transfer, not good diversity at scale.

## Theater

`theater_story.py` adds a local finite projection model, readable prompt text,
character memory, audibility and adjustable costume size. A shadow changes
through manipulation of a physical cutout relative to a charged lamp. Mina must
visit its source before the scene can finish. A whisper does not teach a line
in a noisy room; the book must be carried to the stage and read. A blank page
must also be inspected before a wordless replacement is chosen. The welcome
opens a real modeled door and admits Jo. A poorly fitting crown falls to the
tray; resizing consumes a clip, otherwise it is displayed on the royal chair.

The local v1 ten was preserved; v2 corrects one awkward pronoun phrase before
the first paid test. Manual reading found the no-problem crown variants weakest:
confidence changes, but the external obstacle is slight. Terra rated these 7
storytelling versus 8 for the more consequential plots. Overall storytelling
was 7.8/8.0, diversity 4/4. The many repeated shadow scenes remain obvious.

## Limits and next measurements

An exhaustive local audit, `replication_space_v1.json`, executes all 512
greenhouse Boolean configurations and all 96 theater configurations, then walks
every renderer choice branch. It finds hard ceilings of **34 greenhouse texts /
10 action paths** and **28 theater texts / 8 action paths** for these versions.
The 100-position batches already contain 26 and 25 texts respectively. These
are not just unlucky random samples. More seeds or synonyms cannot create new
causal plots; additional goal interactions or authored developments are needed.
The count is conditional on these exact generator/renderer source hashes and
their finite Boolean input domains, not a claim about all possible future scripts.

- Scenes are authored purpose policies over explicit rules, not general planning.
- Paragraph provenance and exact replay do not prove every sentence's entailment.
- Greenhouse and theater extend local registries; shared physical semantics,
  gen6, gen7 and legacy engines are unchanged.
- The sampler takes up to six supported QA conversations per story, all
  single-turn. Harbor's hundred has four five-question declined-loan cases;
  the two replications have six for every story. No multi-turn success claim.
- Full regression after adding both generators, comparison/audit tools and the
  theater QA distance correction: 461 tests passed.
- Fresh 100-position batches start at seed 10000 for each script. Keep duplicate
  positions. Cross-script measurement must not be confused with within-script
  diversity. Do not relabel setting changes as new plots.

The full hundred-story and pooled baseline is now complete; see
[final findings](../replication_pooled_v1/FINDINGS.md). Structural diversity is
still an open improvement goal. All hundred theater stories and trace hashes
were rechecked unchanged after the subsequent QA-only corrections.

Commands from the repository root:

```bash
./.venv/bin/python -m storyscenes.greenhouse_story --seed 6 --qa
./.venv/bin/python -m storyscenes.theater_story --seed 4 --qa
./.venv/bin/python storyscenes/harbor_trial.py prepare --world greenhouse --count 30 --seed 1000 --out storyscenes/runs/NEW_BATCH
./.venv/bin/python storyscenes/harbor_trial.py judge --out storyscenes/runs/NEW_BATCH --api-key-file .API_KEY --concurrency 4
```

Only run one judge process at a time against the shared campaign ledger.
