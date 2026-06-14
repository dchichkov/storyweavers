# Story Quality & Fidelity Evaluation (Agent-as-Judge)

This document defines **how to measure the quality of gen6-generated stories**.
Coverage (`coverage.py`) tells you *whether* a kernel runs; this eval tells you
*how good the resulting story is* and *how faithful it is to the original*.

It is an **agent-as-judge** protocol: a coding agent reads this rubric, looks at
(original story, kernel, generated story) triples produced by `quality.py`, and
assigns scores. This is **synthesis-time** evaluation — it does not run an LLM at
generation time, so it respects the project's "no LLMs at runtime" rule.

Because story IDs are stable and generation is deterministic, a fixed `--seed`
always selects the same stories, so scores are **comparable across runs** (e.g.
before/after a kernel pack or an engine change).

---

## Quick start

```bash
# 1. Produce a 100-story gradeable worksheet (mix of coverage levels).
python quality.py --sample -n 100 --seed 42 --out quality_runs/run_001.jsonl

# 2. Grade it: for EACH record in the JSONL, fill in `scores`, `usable`,
#    `defects`, and `notes` per the rubric below (see "How to grade").

# 3. Aggregate.
python quality.py --report quality_runs/run_001.jsonl
```

Each worksheet record looks like this (you edit the fields marked ✎):

```json
{
  "id": "data00:1032",
  "coverage": {"covered": 7, "total": 8, "ratio": 0.875},
  "kernel": "Sue(Character, girl, ...)\n...",
  "original": "Once upon a time, there was a little girl named Sue. ...",
  "generated": "Once upon a time, there was a little ... girl named Sue. ...",
  "scores": {"grammar": null, "coherence": null, "fidelity": null,        // ✎
             "completeness": null, "naturalness": null, "overall": null}, // ✎
  "usable": null,        // ✎ true/false: acceptable in a training dataset?
  "defects": [],         // ✎ subset of the defect tags below
  "notes": ""            // ✎ one short sentence on the main issue, if any
}
```

---

## What we are measuring

Kernels are a *lossy compression* of a story, so the goal is **NOT verbatim
reconstruction**. A good generated story is one that (a) reads as a coherent,
grammatical children's story on its own, and (b) preserves the original's
characters, key events, and emotional arc. We score both intrinsic quality and
structural fidelity.

## The rubric — six dimensions, each scored 1–5

Use the whole scale. `3` = "acceptable but flawed". Anchor every score to the
descriptions below.

### 1. `grammar` — sentence-level well-formedness
- **5**: every sentence grammatical; correct articles (a/an), verb tense,
  agreement, pronoun case.
- **3**: mostly fine; 1–2 minor slips ("the her ball", an odd article).
- **1**: frequent broken grammar, verbed nouns ("Tom gratituded"), word salad.

### 2. `coherence` — does it hang together?
- **5**: sentences connect logically; pronouns resolve to the right character;
  no contradictions; no stutter/repeats.
- **3**: readable but choppy; a transition or two missing; one ambiguous pronoun.
- **1**: disjointed; contradictory; repeated lines; can't tell who "she" is.

### 3. `fidelity` — does it preserve the original?
- **5**: same characters, the key events, and the same emotional arc/outcome.
- **3**: same cast and gist, but a major beat is missing or altered.
- **1**: unrelated to the original, or the arc/outcome is contradicted.

### 4. `completeness` — did every kernel render cleanly?
- **5**: no garbled output — no "Something X happened", no literal concept dumps
  ("there was indifference jam"), nothing obviously dropped.
- **3**: one fallback-ish or bare-concept line, but the story survives it.
- **1**: multiple kernels degraded to fallback / literal concepts; gist lost.
- (Tip: `coverage.ratio < 1.0` predicts trouble here, but a good fallback can
  still earn a 4–5, and a fully-covered story can still be a 2.)

### 5. `naturalness` — does it read like a story?
- **5**: flows like a real TinyStories entry; varied phrasing.
- **3**: a bit templated/listy but acceptable.
- **1**: an obvious list of template sentences; robotic.

### 6. `overall` — holistic single number
Your gestalt judgment of the generated story as a children's story. Not a strict
average — weight what matters most for this story.

### `usable` (boolean)
Would you include this generated story in an LLM training set without
embarrassment? `true`/`false`. This is the bottom-line product question.

### `defects` (tags — pick all that apply)
Controlled vocabulary so recurring problems are quantifiable across runs:

| tag | meaning |
|-----|---------|
| `verbed_noun` | an abstract noun got conjugated ("warmthed", "joyed") |
| `missing_kernel_fallback` | "Something X happened." / generic fallback line |
| `literal_concept` | a bare concept jammed in ("there was indifference") |
| `pronoun_error` | wrong/ambiguous pronoun, or name where a pronoun belonged |
| `double_subject` | "Leo was Leo really wanted…" |
| `clause_in_noun_slot` | a whole clause sits in an object slot ("wanted Nemo explored the coral") |
| `repetition` | a sentence/line repeats |
| `article_error` | "the her ball", "a apple" |
| `dropped_content` | a key original beat is absent |
| `incoherent_transition` | jarring jump between sentences |
| `wrong_subject` | an action attributed to the wrong character |
| `other` | anything else (explain in `notes`) |

---

## How to grade (per record)

1. Read `original` to understand the intended story (characters, events, arc).
2. Read `generated`. Judge it **as a standalone children's story first**
   (grammar, coherence, naturalness), **then** against the original (fidelity,
   completeness).
3. Fill `scores` (all six, 1–5), set `usable` (true/false), add any `defects`
   tags, and write one short `notes` sentence naming the main issue (or "clean").
4. Be calibrated and honest — the point is to find regressions and prioritize
   fixes, not to inflate the number. A `5/5` story has *no* issues you'd fix.

### Parallelizing across many agents
The worksheet is line-oriented JSONL, so it shards trivially: give each agent a
slice of lines (or its own `--seed`), have each write back its graded lines, then
`cat` the shards into one file and run `--report` on the whole. With N agents you
can grade N×100 stories in one pass.

---

## Reading the report & target thresholds

`python quality.py --report <file>` prints per-dimension means, the `usable`
rate, **overall broken down by coverage tier** (full / high / partial), and a
**defect-frequency** table plus the lowest-rated stories to triage.

Suggested gates (tune as the engine matures):

| metric | red | ok | good |
|--------|-----|----|------|
| `overall` mean | < 3.0 | 3.0–3.8 | ≥ 3.8 |
| `usable` rate | < 50% | 50–75% | ≥ 75% |
| `overall` on **full**-coverage tier | < 3.5 | 3.5–4.2 | ≥ 4.2 |

The **full-coverage tier** is the engine's ceiling (every kernel implemented);
if that is low, fix the *generator/kernels*, not coverage. A low **partial**
tier with a healthy full tier means: implement more kernels (or improve the
fallback). The **defect table** points directly at what to fix next — feed the
top tags back into a quality pass (see AGENTS.md "gen6 Quality Pass").

---

## Workflow tie-in

- Run a baseline (`--seed 42 -n 100`) and commit the graded worksheet under
  `quality_runs/` so future runs compare against it.
- After a kernel pack or engine change, re-run the **same seed** and diff the
  report. Quality must not regress; the defect table should shrink.
- Promote consistently-`5/5` stories to pinned regression tests (see AGENTS.md
  "Pinning Good Stories as Tests").
