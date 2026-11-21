# Entity-specific event lines: first factorization pass

Implemented annotations and per-entity event lines for the seven defined
storytelling worlds. Each entity gets its own perspective on shared events,
with role tags, physical changes, counterpart entities and declared dependency
boundaries. The source stories and their generation policy are preserved.

## Results

Seeds 3000–3019, expanded grammar, original manual heads, past tense:

| Measure | Result |
|---|---:|
| Stories replayed and annotated | 140 |
| Event occurrences | 1,808 |
| Pack-qualified event kinds covered | **119 / 119** |
| Participating entity-line instances across the stories | 1,181 |
| Events involving multiple tagged participants | 1,771 |
| Tests passing | **104** |

The entity-line count includes repeated entity roles across seeds, not 1,181
distinct character types. Most events connect an actor to an object or another
person; the high shared-event count does not mean every event depends on every
entity in its story. Frame slots are conservative, sometimes coarse evidence.

The first pass used frames, speakers, references and full replayed effects. The
second added explicit typed grammatical subjects and paired listener metadata.
It recovered coactors such as Jun in “Mina and Jun searched…” and Ms Alvarez in
the atlas-reservation sentence, where the coarse event frame names Mina as
actor. Both the original frame role and the grammatical role are retained with
provenance rather than silently rewriting the frame.

All 140 texts and physical event effects are identical between tagging passes.
Seven preselected stories also match the pre-task archived generation exactly,
including final worlds and every sampled next-word distribution. Existing
grammar, head, story, branch, QA and portable suites remain green. This is a
structural annotation result, not a literary quality improvement claim.

## What is now factorized

One library checkout event appears on three entity lines:

| Entity | Local perspective | Physical change |
|---|---|---|
| Ms Alvarez | Source holder, actor, grammatical subject | Releases the book |
| Jun | Destination holder | Receives the book |
| Whale book | Moved object | Holder: Ms Alvarez → Jun; gains `checked_out` |

All three point to the same event ID. “Releases” and “receives” here describe
physical possession; no separate legal ownership or motive is inferred.

The pottery projection also preserves one `cup` entity ID when its noun changes
to `bowl`. Replaying full entities captures this change, which the ordinary
compact event snapshots omit. Concept magnitude changes are attached to their
physical people in the same way.

The exports distinguish actual role/effect participation from mere mention,
QA context and declared causal context. They include internal, unnarrated
events, so an object's line retains drying, firing, cooling and returns that
short prose may omit.

## Local alternatives already present in the defined stories

The [Mateo examples](refined/local_variants.md) extract the first occurrence of
each music branch in the fixed seed range:

- Receive invitation → decline public performance → hear Nia choose a solo → applaud.
- Receive invitation → decline public performance → offer a written rhythm → write it → applaud.
- Receive invitation → decline public performance → offer private playing → collect instrument → play together → respond → return instrument.

These are **local projections of existing branches**, not newly generated
replacement plans. Their initial state and surrounding events differ. The
[machine-readable slices](refined/music_partner_variants.json) retain those
entry/exit states, joins and declared dependencies instead of claiming that
the alternatives can be swapped without checking consent and the other lines.

## What remains coupled

The new `local_slice` API exposes what a future local replacement must connect
to: counterpart events, object movements, dialogue, flag requirements, external
dependencies and outgoing effects. The real guards still need to approve the
result. Global flags are not yet factorized, and the extracted dependencies are
not a complete read set for arbitrary Python guard code.

Thus we can now **inspect and supply an entity-local line as structured data**.
Independent execution, safe replacement, cross-world role remapping and inferred
lines remain future work. An attention mechanism could retrieve these local
patterns from their role/state tags and bias eligible successors. No new
attention weights or local-line receiver were introduced in this pass.

## Browse the outputs

- [Library](refined/library.md)
- [Pottery](refined/pottery.md)
- [Music](refined/music.md)
- [Rescue](refined/rescue.md)
- [Kite](refined/kite.md)
- [Key](refined/key.md)
- [Greenhouse](refined/greenhouse.md)
- [119-entry observed event/tag catalog](refined/catalog.json)
- [API and schema guide](../../storytelling/EVENT_LINES.md)

`refined/entity_lines.jsonl.gz` contains all 140 final graphs. Individual JSON
graphs and protagonist slices accompany each Markdown sample. `verification.json`
records counts and comparisons; `refined/source_manifest.json` identifies the
source files. Root-level samples retain the initial tagging pass for comparison;
use `refined/` for the final annotations.
