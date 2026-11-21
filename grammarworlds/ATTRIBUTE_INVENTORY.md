# Recent attributes and planned storytelling attributes

Status: 2026-11-08. This lists the recent symbolic-generation work, rather than
all fields in the repository. **Candidate** means available before sampling;
**observed** means derived from committed history or a completed source document.
An attribute being present does not mean a head or planner already consumes it.

## Implemented before this annotation pass

| Group | Actual fields / paths | Scope and behavior |
|---|---|---|
| Grammar | `pos`, `syntax_role`, `nominal`, `modifier`; `clause.subject`, `.predicate`, `.tense`, `.polarity` | Candidate grammar attributes. Missing categories remain explicit. |
| Action meaning | `action.lemma`, `.arguments`, `.modality`, `.modifiers`; `action_scope` | Candidate finite/embedded action structure. Availability depends on the construction. |
| Reference and physical state | `entity`; `entity_features.id`, `.noun`, `.kind`, `.number`, `.pronoun`, `.location`, `.properties`, `.state`, `.memes`; `state_scope` | Candidate bindings and current receiving state, normally `before_scene`. Physical holding/location is not a general legal-ownership model. |
| Speech and assertion | `quoted`, `speaker`, `listener`, `assertion`, `unresolved` | Distinguishes quoted, hypothetical, negated and narrated candidate content. Speech does not automatically execute its embedded action. |
| Fine event | `event.name`, `.source_kind`, `.roles`, `.causes`, `.tags`, `.status`, `.scope` | Candidate scene meaning and coarse actor/patient/instrument/destination bindings. Clause roles may be more detailed than frame roles. |
| Joint uncertainty | Word-choice `probability`; `annotated_choices[].attributes`, `.probability`; emitted `candidates[].attributes`, `.probability` | Distributions over complete word/attribute bundles and conditional meanings. Not an independent probability for every field. |
| Position | `position.story`, `.token`, `.sentence`, `.in_sentence`; `rotary.token`, `.sentence`, `.in_sentence` | Emitted-token positions and symbolic ring phases. Relative offsets are computed by the positional adapter. Not elapsed world time. |
| Intact source memory | `memory.event_id`, `.event_name`, `.participants`, `.entity_tags`, `.entity_observations`, `.prior_silent_events`, `.mapping_rules` | Observed event references and changes attached to original tokens. Silent events have token-boundary anchors. Source text is preserved. |
| Native dependencies and changes | Event `dependencies`, `effects`, `movements`, `global_contract`, `guard_reads_complete` | Observed/replayed records, with explicitly incomplete guard-read coverage. Distinct from proposed action semantics. |
| Strict operation transfer | `event.expected_effects`, `.effects_scope`, `.effects_complete`, `.transfer_policy`; `attribute_transfer` audit | The earlier reviewed-operation adapter recomputes target fields. Expected effects are proposed, not completed facts; these fields are not universal to all runtimes. |
| Joined native transfer | Unit `mapping`, `prefix`, `references`, `leakage`; event `transfer.source_scenario`, `.source_kind`, `.source_event`, `.native_event` | Records source provenance, receiving bindings and explicit imports. Native guards/effects still execute. |
| Semantic event scales | Candidate `event_scales.memberships[]` with `id`, `scale`, `name`, `status`, `carrier`; `relations`, `persistence` | Opt-in `multiscale=True`: story / episode / entity-chain context, above the existing fine event and tokens. Chains currently inherit episode completion. |
| World time | Candidate `event_scales.duration`, `.start_seconds`; committed event `time.start_seconds`, `.end_seconds`, `.duration_band`, `.duration_seconds`, `.distribution`, `.relation` | Estimated duration distributions and sampled serial time. Higher-level duration estimates are not added again. |
| Persistent commitments | `narrative.commitments`: `name`, `scale`, `carrier`, `parents`, `checks`, `status`, `started_at`, `achieved_at`, `deadline_seconds`, `persistence`; episode `offers` | Physical/native-event completion checks. Proposed/active/achieved/blocked/abandoned states. Optional timestamps appear when applicable. |
| Receiving goals / coarse outlines | `narrative.mission`: `name`, `carrier`, `needs`, `deadline_seconds`, `status`, `overdue`; each need has `name`, `checks` or `offer`, `requires`, `status`, `evidence`, optional `achieved_at` | Existing coarse planner consumes these. `event_scales.primary_goal` exposes current mission context to candidate tokens. Coarse outlines share a protagonist; shared objects across stages are not yet required. |

The existing sampler preserves correlations between candidate meanings. Some
heads use entity bindings and physical state; the coarse planner uses goal
progress and time. General plot-based reranking is not yet implemented.

## Added in this pass

Plot annotations are available in two forms:

- Candidate bundles: `plot`, enabled by `plot_annotations=True` or
  `--plot-annotations`, including END candidates for silent events.
- Historical memory: `events[].plot`, `tokens[].memory.plot`, and
  `plots.nodes`, added by source annotation/export.

| New field | Meaning | Evidence / limits |
|---|---|---|
| `plot_id` | Identifies a source plot instance, namespaced for transfer. | Not yet a unified receiving-story plot identity. |
| `source_scenario` | Origin of the authored narrative reading. | Provenance, not an instruction to reproduce all source events. |
| `archetypes[].name`, `.fit`, `.basis` | Associations with the nine-category inventory. | Current matches are explicitly `partial`, based on authored interpretation; an empty list is allowed. These are not calibrated probabilities. |
| `local_pattern` | More specific trajectory, e.g. `failed_attempt_diagnosis_changed_approach`. | Authored per source world. |
| `goal` | Human-readable story-level goal. | Current source goal label; not a complete executable plot contract. |
| `roles` | Physical IDs for protagonist, helper/partner, recipient, central object, clue object, instrument, etc., where applicable. | Bound to receiving entities on transfer. Cast roles do not imply participation in every individual event. |
| `unbound_roles` | Role groups with no available carrier. | Explicit missing information. |
| `stakes.description`, `.basis` | Why failure matters in this source story. | Authored interpretation; not a newly inferred world fact or measured utility. |
| `role` | Event function: desire, lack, promise, setback, failed attempt, threat, conflict, clue, discovery, choice, revision, help, attempt, decisive action, payoff, final image, supporting action. | 191 fine-event kinds have explicit authored readings; 58 logistical kinds retain a neutral supporting role. |
| `stage` | Setup, complication, development, resolution, aftermath or support. | A function label, not an enforced monotonic stage machine. |
| `basis` | `authored_event_reading` or `neutral_default`. | Makes explicit readings distinguishable from coverage defaults. |
| `incoming_links[].source_event`, `.relation`, `.basis`, `.mechanically_verified` | Earlier event evidence for responds-to, uses-discovery, payoff-of, ending-evidence, changes-strategy and related narrative links. | Only actual earlier occurrences are referenced. Narrative links are explicitly **not mechanically verified causal claims**. |
| `scope`, `status` | Candidate `receiving_prefix` / `proposed`; historical `completed_source_observation` / `observed`. | Separates prediction from retrospective knowledge. |
| `observed_consequences` | Entity field changes copied from replayed event effects. | Historical only; never inserted into live candidates as completed outcomes. |
| `native_dependencies`, `native_guard_reads_complete` | Original engine dependencies and their completeness flag. | Historical only; distinct from authored narrative links. |

Document plot nodes also contain `rationale`, `event_ids`, and the realized
`links` with `target_event`. Joined nodes use `scope: transferred_source_arc`;
annotating several imported arcs does not claim the combined story is coherent.
`plot_prior_events` preserves references to earlier receiving history when a
resumed segment needs evidence outside its own token document.

Example, simplified from an actual source annotation:

```json
{
  "plot_id": "repair/plot",
  "archetypes": [{"name": "mystery", "fit": "partial", "basis": "authored_interpretation"}],
  "local_pattern": "failed_attempt_diagnosis_changed_approach",
  "goal": "Repair the trolley so the load can be moved",
  "role": "decisive_action",
  "stage": "resolution",
  "roles": {"protagonist": ["hero"], "central_object": ["cart", "wheel"]},
  "incoming_links": [{"source_event": 5, "relation": "uses_discovery", "basis": "authored_narrative_reading", "mechanically_verified": false}]
}
```

The reference points back to the actual `diagnose_string` event. The subsequent
`quiet_wheel` event can be labeled ending evidence for the repair. These labels
are available to future selection/reranking; this pass does not use them to
claim improved generated storytelling.

## Planned, not implemented

Proposed field names below are design candidates, not current API promises.

| Priority | Planned attributes | What they would enable |
|---|---|---|
| 1 | `shared_bindings`, `binding_scope`, `same_entity_as`, `recipient_binding` | Require `adapt(object=X) → give(object=X)` and preserve relevant recipients/tools across imported stages. Existing source-role mappings do not yet enforce this across unrelated arcs. |
| 1 | `receiving_plot_id`, `active_stage`, `stage_preconditions`, `stage_effects`, `allowed_transitions`, `completion_evidence` | Execute a chosen plot trajectory over receiving state. Existing `plot.stage` is only an annotation. |
| 1 | `setup_refs`, `payoff_requirements`, `open_obligations`, `closure_status` | Track promises, planted details and unresolved questions; prevent an ending that leaves the main setup unpaid. Current `payoff_of` links are retrospective readings. |
| 2 | `desired_outcome`, `underlying_need`, `belief`, `belief_evidence`, `expectation`, `choice_alternatives`, `cost`, `sacrifice` | Connect character decisions to stakes and changes in understanding. Existing state flags/memes are not a general belief or motivation model. |
| 2 | `known_by`, `revealed_to_reader`, `clue_supports`, `hypothesis`, `contradicts`, `reveal_conditions` | Separate author knowledge, character knowledge and reader knowledge; support genuine mystery construction. Current `clue_object` is only a cast role. |
| 2 | `narration_function`, `establishes`, `reminds_of`, `explains_link`, `ending_image_for` | Ensure prose expresses the premise, consequential choice and final change. Existing `final_image` labels do not guarantee adequate narration. |
| 3 | `plot_compatibility`, `tension_change`, `payoff_coverage`, `repetition_penalty`, `interpretation_weight` | Rerank supported event/token alternatives by plot context while preserving a normalized distribution. No plot weights have been learned or calibrated. |

The most useful next experiment is shared object/recipient binding plus an
executed plot-stage contract. Merely adding more labels will not make the
sampler consume them or make the prose express their relationships.

## Reproduction and references

```bash
.venv/bin/python -m grammarworlds.plot_annotation_export --out /tmp/plot-annotations
.venv/bin/python -m grammarworlds.storytelling --scenario repair --plot-annotations --multiscale --json
.venv/bin/python -m unittest grammarworlds.test_plot_annotations -v
```

See [the complete annotated examples](runs/plot_annotations_20261108/report.md),
[semantic token attributes](storytelling/ATTRIBUTES.md), and
[event scales](EVENT_SCALES.md). The nine-category working inventory takes the
seven named archetypes plus the separately discussed mystery and rebellion
categories from Booker's book; our executable interpretations and event labels
are our own. [Publisher's contents](https://www.bloomsbury.com/uk/seven-basic-plots-9781441116512/).

## Implementation update — 2026-11-09

The following parts of the planned list above are now implemented for the two
[executable plot contracts](PLOT_EXECUTION.md). The earlier tables describe the
2026-11-08 baseline; generalizations beyond these contracts remain planned.

| New executable field | Current behavior |
|---|---|
| `plot_execution.kind`, `.name`, `.carrier`, `.bindings` | Receiving plot identity/type and persistent physical object/recipient identities. |
| `plot_execution.active_stage`, `.stages` | Each stage has `allowed_roles`, `condition`, `requires`, `requires_link`, `status`, and event/binding evidence. Native execution advances the state. |
| `plot_execution.obligations` | Setup event, shared bindings, open/resolved state and the actual resolution event. |
| `plot_execution.knowledge_evidence` | Earlier executed discoveries linked to the plot's setback; used to admit a changed approach. |
| `plot_execution.character_knowledge` | New native `knows_*`/`understands_*` state changes with event provenance. No general false-belief representation yet. |
| `plot_execution.reader_knowledge` | Narrated event IDs and typed referents; distinct from character knowledge. |
| `plot_execution.narration_requirements` | Stage event, expected relevant entities, observed typed entities and satisfied/missing status. |
| `plot_execution.status` | Active, blocked, structurally complete, narration incomplete, achieved, or explicitly abandoned. |
| Event `plot_transition` | Stage/index and the bindings accepted at this actual event. |
| Candidate `plot.receiving_plot` | Prefix-only receiving plot state, available before word sampling. |
| Decision `completion_in_source_suffix`, `deadline_probability`, `score`, `probability` | Bounded native lookahead, time compatibility and normalized continuation weights. Predictions, not observed future facts. |

These fields now **affect candidate support and selection**, rather than merely
being exported. They do not add new word-head weights. General shared-variable
unification, full archetype grammars, broad belief/reader models, and calibrated
plot/style scoring remain unimplemented.

## Presentation update — 2026-11-10

Titles, openings and closings now have separate annotated-word distributions
under `result.presentation.title`, `.opening`, and `.closing`. They use the
existing `AttributeForest`, with each component's `trace`, `attributes`, and
normalized `alternatives`. Body/event candidate tables remain unchanged.

| Presentation field | Meaning |
|---|---|
| `narration_role`, `style`, `opening_style`, `closing_style` | Framing function and authored form; the applicable style field appears on opening/closing candidates. |
| `carrier`, `referents`, `entity` | Physical protagonist, construction references and the entity expressed by this token, when applicable. |
| `evidence_scope` | Initial-world identity/location for openings; final-world context for titles; completed narration for closings. |
| `source_event` | Actual first/last scene used by an empty immediate/final-image construction; otherwise null. |
| `assertion` | `narrative_framing`, never a new executed physical event. |
| `pos` | `END`, `PUNCT`, or currently `X`; framing semantics and entity references are authored, full lexical POS annotation remains to do. |

`result.story` is the presented text; `raw_story` preserves the generated body.
The separate presentation trace is sampled after body generation and does not
feed future information into native token prediction or alter plot completion.

## Beat update — 2026-11-13

| Field | Implemented meaning |
|---|---|
| Event `beats`; token `memory.beats` | Authored scene readings with kind, experiencer, object, preceding event, speech act, phase and evidence scope. |
| Token `memory.beat_candidates`; live candidate `beat` | Token-specific beat interpretations with conditional probabilities; candidate semantics are separate from completed-source observations. |
| Event `beat_decision` | Eligible constructions, explicit immediate-action alternative, probabilities and selected construction. |
| `World.narrative.beats` | Persistent cap/use count, expanded triggers, physical detail setups, executed beat history and uttered requests/proposals. |
| Detail `setup_event`, `entity`, `initial_state`, `results`, `used` | A visibly planted detail and permitted later uses over the same carrier. |
| Historical `detail_links` | Earlier setup, later result and observed entity state; authored interpretation backed by replay. |
| Added beat `planned_event` | A proposed commitment's selected native action, not a fact observed before execution. |
| Beat QA `event_ids`, `entity_ids`, `evidence` | Both visibly narrated ends of the relation, with text offsets checked against the story. |

See [BEATS.md](BEATS.md) for scope, controls and limits. Full false-belief,
concealment and general automatic motif extraction remain future work.


## Beat/presentation refinement — 2026-11-15

| Field | Current consumer and interpretation |
|---|---|
| Source row `presented_story`, `raw_story`, `title`; `presentation.body_offset`, `.body_length` | CLI/reports show title/opening/body/closing; raw body and its QA/token offsets remain intact. Standalone `story` remains raw, while assembled plot `story` is framed. |
| `beats.schema='story-beats-v2'` | Strict validation of per-candidate readings and original posterior identity/probability. |
| Beat `action_actor`, `experiencer`, `experiencer_basis`, `source_scenario`, `source_kind` | Physical doer and human perspective can differ; speaker evidence is checked separately. |
| `memory.beat_candidates[].attributes`, `.probability`, `.beat`, `.basis` | Reading follows this alternative's own event/roles. Historical reconstruction is explicitly labeled; original candidate attributes and probabilities are preserved. |
| Detail `setup_in_document`; `prior_setup_events[].text_available=False` | Resumed segments can inherit a setup/state, but cannot claim its text appears locally. |
| Beat `discovery_event`, `related_events` | A proposal can depend on an earlier authored discovery across intervening scenes. Evidence must precede it and use compatible source bindings. |
| Beat `proposal.lemma`, `.object`, `.recipient` | Concrete transfer intention, consumed by the optional semantic grammar; not a completed transfer. |
| Detail `callback.state`, `.past`, `.present`, POS lists and `.predicate` | Authored state-gated realization for ten additional motifs. Stored when planted, so later catalog changes do not rewrite historical memory. |
| Optional token `authored_pos` → `pos`, `lexical_lemma`, `syntax_role`, `clause`, `action`, `action_scope`, `hypothetical`, `evidence_event`, `annotation_status` | Live annotated-word candidates distinguish utterance, request, proposal, recollection and unresolved vocabulary. Requests/proposals never execute their embedded actions. |
| Beat QA `evidence` | Exact earlier text plus selected beat prefix, excluding the subsequent action. Display offsets are derived explicitly by `presentation_evidence`. |
| Export `beats.export_replay` | Recorded-policy replay scope and verification; full narrative when archived, limited native physical replay for older documents. |

No general belief, intention-fulfillment, causal explanation, irony or suspense
model has been added. Immediate action remains an option, and beat budgets are
caps rather than quotas. Refer to [BEATS.md](BEATS.md) and the
[ten-round report](runs/beats_20261115/REPORT.md) for examples and limitations.

## Authored content prototypes — 2026-11-16

These fields apply to the opt-in crafted edition, not every existing pack.

| Field | Meaning and consumer |
|---|---|
| Candidate `storycraft.scope`, `.function`, `.desired_outcome`, `.motivation`, `.proposed_cost` | Authored narrative reading of a proposed event; available in the correlated token distribution, not asserted as an executed future. |
| `storycraft.earlier_events`, `.causal_predecessors`, `.open_obligations` | Prefix-only history and direct declared prerequisites. Physical and obligation guards constrain which candidate frames exist. |
| `World.narrative.storycraft.obligations` | Carrier, setup event, open/resolved status and resolution event; blocks duplicate setups, unsupported closures and premature endings. Resolution does not necessarily mean the original wish succeeded. |
| `World.narrative.storycraft.history`, `.completed`, `.title` | Executed event/function/cost readings and completion; presentation uses authored title and actual final image. Costs are authored interpretations, not inferred utilities. |
| Candidate `speech_act` | Name, speaker, listener and `candidate_utterance` scope; an invitation/promise remains separate from its eventual response/fulfillment. |
| Candidate `narrative_role` | Fragment role such as desire, reaction, decision or final image. |
| `action_scope='authored_fragment'`, `annotation_status='authored_fragment'` | Coarse authored semantic unit, potentially more than one clause. Not a complete word-level syntactic parse. Unknown POS remains `X`. |

[STORYCRAFT.md](STORYCRAFT.md) documents the supported controls, physical
contracts, evidence limits and remaining transfer work.

## Executable decision beats — 2026-11-19

These fields appear with `edition='crafted', decision_beats=True`.

| Field | Meaning / consumer |
|---|---|
| Character `memes.Decision_*` | Bounded priorities written by the selected appraisal and read by later event scoring. |
| Candidate `storycraft.decisions.appraisal`, `.forecast_stakes` | Possible interpretation and expected trade-offs; not observed future facts. |
| `.prior_appraisals`, `.observed_costs`, `.required_utterances` | Prefix evidence available before this candidate event. Later facts are excluded. |
| Candidate `dialogue_contract` | Key, actual speaker, listener and act for an authored utterance construction. |
| Candidate `narrative_detail` | Carrier, semantic key/meaning, setup/payoff/reminder phase and applicable compression weights. |
| Event evidence `decision_beats` | Per-dimension priority, expected stake, contribution and source appraisal event; reports whether attention scoring is enabled. |
| Event `narrative_decision` | Selected motif, utterance and reminder constructions; replay recomputes them from the prefix. |
| `World.narrative.storycraft.decisions` | Appraisals, actual utterances and resolutions, observed costs, visible details, earned payoffs and selected/omitted reminders. |
| Exported event `decision_beats.scope='replayed_source_event'` | Verified observations copied to intact annotated source documents, distinct from live candidate attributes. |
| Export dependencies `appraisal_evidence`, `dialogue_*`, `payoff_setup`, `reader_knowledge` | Earlier evidence/utterance/setup IDs. These enrich local projections; Python guard-read coverage remains incomplete. |

No arbitrary-English semantic inference is claimed. A different meaning must
be authored explicitly; this policy cannot infer that two untagged sentences
are paraphrases.
