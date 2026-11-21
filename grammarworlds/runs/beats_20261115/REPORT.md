# Story beats: ten further refinements — 2026-11-15

Titles, openings and closings now appear in standalone generation, the CLI and the experiment reports. The framing was previously attached to joined plot results but missing from the source-story report path. Raw story text, replay, token offsets and QA evidence remain separately available.

The ten additional rounds below improve grounding and reuse: character perspective, candidate-specific attributes, functional dialogue, persistent details, typed optional constructions and QA. They do **not** establish a measured literary-quality improvement. Callbacks still sometimes repeat outcomes, and authored source plots still dominate.

## What changed in practical terms

- A frame’s physical actor is not automatically the person who experiences a beat. A falling shade cloth can affect a person without becoming the experiencer.
- An object in hidden frame metadata is not automatically introduced to the reader. The library no longer inserts an inspection of an unseen mitten.
- A proposal names a real action/tool, such as “I will give you the lantern.” Saying it is hypothetical; native execution determines what actually happens.
- Optional tokens carry clause, action, participant and scope attributes alongside their distribution. The object of “try the torch” belongs to the proposal, and a wearable cape is not its own wearer.
- A detail can survive transfer into a resumed story segment. Its physical carrier and historical setup survive; unavailable earlier text cannot support local QA.
- Concrete motifs now cover 16 details in 13 of 20 worlds, with at most one optional reminder per source arc. A budget is a cap, not a quota.

## Presentation preflight

The [preflight](preflight/) reformats 18 saved examples while preserving their bodies; the November 13 top-level report now links that corrected display edition. This is separate from the ten rounds. Source rows expose `presented_story`; `story` remains the raw body. Joined plot results expose framed `story` and retain `raw_story`. `presentation.body_offset` maps between them. The CLI defaults to framing and supports `--raw`.

## Ten actual code-and-sample rounds

Each link contains sampled reports, compressed traces, code copies and a hash manifest. Sample times record the experiment run, not the duration of all implementation/review work. Multiple revisions inside rounds 02, 08 and 10 are retained rather than presented as extra rounds.

| Round | Change | Samples | Evidence |
|---|---|---:|---|
| 1 | **Human perspective and actual speech evidence**. Separate physical actor from experiencer; require the actual authored speaker. | 12 | [Report](round01/report.md) |
| 2 | **Candidate-specific semantics**. Each posterior alternative retains its own event interpretation, identity and exact probability; strict corruption checks. | 8 | [Report](round02/report.md) |
| 3 | **Grounded, nonduplicated dialogue**. React to earlier affected objects, require access/co-location, and suppress extra dialogue when the native speaker already voices the response. | 16 | [Report](round03/report.md) |
| 4 | **Detail continuity and pacing**. Carry same-entity setups across joined segments without inventing local evidence; at most one reminder per source arc. | 12 | [Report](round04/report.md) |
| 5 | **Ten more concrete motifs**. Expand 6 motifs in 3 worlds to 16 in 13; callbacks require stored setup and a current physical state. | 20 | [Report](round05/report.md) |
| 6 | **Typed optional constructions**. POS, clause/action arguments, scope, hypothetical status and setup evidence enter the live annotated-word distribution. | 12 | [Report](round06/report.md) |
| 7 | **Within-scene reference clarity**. After a subject switch, keep a full-name alternative; preserve same-subject pronoun choices and quoted speech. | 10 | [Report](round07/report.md) |
| 8 | **Concrete, discovery-backed proposals**. Name a real tool/transfer; bridge authored discovery links across logistics; one proposal per discovery; no generic another-way fallback. | 12 | [Report](round08_final/report.md) |
| 9 | **Precise beat QA and reader visibility**. Validate selected decisions, cite the actual discovery and exact beat prefix, map display offsets, and exclude unseen frame decoys. | 20 | [Report](round09/report.md) |
| 10 | **Historical replay and final review corrections**. Replay archived choices/ledgers with explicit scope; validate discovery links; fix embedded-action object scopes, optional subject coherence, plural titles and spoken-tool QA bindings. | 18 | [Report](round10_final/report.md) |

Round02 initially exposed tiny floating-point overshoots (1.0000000000000002). Validation now tolerates representational error without changing recorded probabilities; the correction is retained in [audit_correction](round02/audit_correction/). Round08_final distinguishes giving a lantern from later trying it and avoids a second proposal from the same clue. Round10_final incorporates the last QA binding correction; the initial round10 remains historical evidence.

## Validation

- **356 tests passed in 197.154s.** [Full log](tests.log).
- [Original archive](annotated_pool/summary.json): 400 documents, 20 worlds, 46,964 tokens and 4,359 native events. Original prose, positions, original candidate attributes and posteriors are preserved. There are 2,983 beat readings.
- The old archive has no expanded-beat decisions or full narrative outcomes. Its replay verifies native guards, flags, entity effects and final entities. Expanded/new archives additionally verify recorded choices and full narrative snapshots. Recorded weights are checked internally, not authenticated against an unavailable historical sampler.
- [Final broad audit](final_audit/summary.json): 80 standalone samples across 20 worlds, seeds 1103/1307, budgets 2/6, past/present; plus 3 joined plots containing 16 resumed rows. All 96 rows replay and re-annotate. 11,307 body word/joint distributions and 1,410 framing steps normalize. 616 QA pairs have exact raw and mapped display evidence.
- Joined plots complete their native contracts with no open obligations or missing required narration. One cap persists across stages. They select pottery or repair throughout each arc; **this is not evidence of novel multi-source plot composition**.
- [Independent review](final_audit/review_40.audit.md): 40 samples, 20 worlds, seeds 701/907. Review found and fixed scope, visibility, plural-title and subject-boundary defects. Some bodies resampled after eligibility changes, so this is an integrated comparison, not an isolated ablation.
- [Reading notes](final_audit/reading_notes.json): all 20 seed 1307/budget 6 bodies were also inspected. Remaining defects include generic reactions, overexplicit callbacks, cross-scene pronouns, weak title relevance and implicit causal links.

## What the samples actually show

Across the 80 final standalone samples, selected-beat counts were 22 stories with 0, 33 stories with 1, 22 stories with 2, 3 stories with 3. Mean use was 1.075; budgets 2 and 6 averaged 1.025 and 1.125 respectively. The immediate-action option is doing real work: increasing the cap does not force more text.

In round10_final, 16/18 nearest-baseline pairs are within 10% of body word count. These baselines come from a fixed 16-seed pool and are matched by length, not quality or identical branch. They are useful inspection pairs, not a controlled literary evaluation. No Luna run or numerical quality gain is claimed.

### A relatively useful reminder

The Shadow

Once upon a time, Miri was at the museum.

Miri said, “I want to show Dot a small shadow.” Kit told Miri, “I would like a dragon.” Miri borrowed the torch. Miri moved the torch. The shadow grew. Miri hesitated. Kit read the instruction label. Miri said, “I need to steady the torch.” Miri steadied the torch with the clay wedge. Miri moved the paper moth toward the screen. The shadow shrank. Dot said, “I could try.” This time, the torch stayed still. Dot held the paper moth beside the screen. The shadow was small.

And that is where this story ends.

The moving torch and later still torch form a visible contrast. The additional hesitation is less distinctive; the native plot already supplies the main causal turn.

### A grounded reminder that is still too explicit

The Cup

Once upon a time, there was someone named Bea.

Bea told Mr Ivo, “I would like to give a cup to Grandpa Len.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped, and the cup was dented. Mr Ivo said, “The cup's wall is thick.” Grandpa Len told Bea, “I could hold a bowl with two hands.” Bea said, “I would like a thumb rest.” With the sponge, Bea shaped the dent into a thumb rest. Mr Ivo fired the cup twice. The cup was cool. Bea handed the cup to Grandpa Len. Grandpa Len poured tea into the cup. The dent had become a thumb rest. Grandpa Len's thumb rested in the thumb rest.

And that is where this story ends.

The dent becoming a usable thumb rest is a meaningful payoff. Stating that transformation immediately before the thumb rests there can over-explain it. Structural grounding alone cannot tell us that the extra sentence earns its space.

## Next storytelling work

1. **Make beats consequential.** Author appraisal/choice alternatives with `desired_outcome`, `cost`, `rejected_alternative`, `decision_reason` and grounded `consequence_ref`. A hesitation should express a specific conflict or change the next choice, rather than only add Caution.
2. **Track what narration already conveyed.** A semantic ledger of narrated entity-state/causal propositions can penalize repeat callbacks while retaining a callback that changes interpretation. This should act on candidate weights before sampling, not trim finished prose.
3. **Make dialogue change the situation.** Link requests to later responses, disagreement to changed plans, promises to fulfillment or explicit failure. Current utterance records deliberately make none of those outcomes automatic.
4. **Extend reference and introduction continuity across events.** Within-scene fixes do not solve “Niko placed the tray. She loosened the nut.” A narrator-state subject model and introduction coverage should feed the grammar.
5. **Evaluate information gained at matched length.** Judge whether an added beat clarifies motive, changes a decision, raises a grounded expectation or pays one off. Keep zero-beat outcomes valid. Compare against compressed native prose as well as longer baselines.

These are proposed next steps, not attributes already implemented in this pass. See the [attribute inventory](../../ATTRIBUTE_INVENTORY.md) and [beat guide](../../BEATS.md) for current fields.

## Reproduce

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario museum --seed 1103 --beat-budget 6 --continuations expanded --qa
.venv/bin/python -m unittest discover -s grammarworlds -t . -p 'test_*.py' -q
.venv/bin/python -m grammarworlds.runs.beats_20261115.audit
.venv/bin/python -m grammarworlds.beat_annotation_export --source grammarworlds/runs/plot_annotations_20261108 --out /tmp/beat-annotation-export
```

No runtime LLM was added. Attention/caution remain carried by physical characters; proposals do not create physical effects, and replay preserves native state constraints. No commit or push was performed.
