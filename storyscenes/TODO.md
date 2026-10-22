# Storyscenes quality and scale gates

## Independent-world scale trial

- Completed `runs/worlds_100_v1/REPORT.md`: **100 new worlds from 131 attempts**,
  **300 graded stories**, story overall **7.183/9** (14 below 6), and **1,800
  graded conversations** at **6.430/9**; 967/1,800 conversations marked usable.
  Dialogue-starting QA scores 6.449/9. This broader sample does not sustain the
  retained two-world 7.75 pilot. All deterministic checks pass, so the next gate
  must measure prose/trace agreement, not just execution or evidence replay.
- Returned cost: authoring **$0.838638**, story grading **$0.487982**, QA grading
  **$1.321549**; total **$2.648169**, plus **$0.170773** held for missing usage.
  All 627 returned calls report Flex; zero cache reads/writes. Authoring projects
  to ~$167.73 per 20,000 mechanically accepted worlds at this yield, excluding
  unresolved charges, evaluation and literary rejection. Do not treat that as
  the price of 20,000 worlds meeting the 7.75 target.
- `world_batch.py` targets 100 newly authored generators, ten per theme, with
  three uniform story positions graded per accepted world. Failed attempts,
  bounded replacements, repairs, and uncertain request reservations remain in
  `runs/worlds_100_v1/`. `world_batch_continue.py` keeps quota slots busy while
  preserving frozen authoring sources and requests; it reuses saved responses
  and quarantines uncertain/capped drafts before moving to a fresh seed.
- First manual sample from every theme exposes `duplicate_handover`,
  `branch_fact_leak`, `weather_drift`, `premature_return`, and
  `raw_fact_fragment`. Examples and exact sample IDs are in
  `runs/worlds_100_v1/manual_notes.md`. Keep this batch frozen for measurement.
- Next engine gate: shared prose cards must support every binding they serve;
  return completion must depend on a preceding loan; the same transfer must not
  be narrated independently by both its bridge and resolution. Validate carried
  object locations alongside custody before relying on ownership QA. These
  are causal/prose alignment defects even when execution and trace QA pass.
- QA needs an `offstage_entity_question` gate: unused ribbon/basket props from
  other paths must not become comprehension questions. Preserve the frozen
  examples in `manual_notes.md` when adding support links from rendered text
  to facts, entities, speech, and events.

## Conversational QA prototype

- Fresh 100-sample semantic trial: stories 7.81/9, conversations 6.81/9,
  dialogue-starting exchanges 7.13/9; Terra marks 314/600 conversations usable.
  All 600 three-turn exchanges pass deterministic trace checks, illustrating why
  those checks do not establish story-only answerability. See
  `runs/conversation_100_v1/REPORT.md`; evaluation cost $0.544181, all 30 calls Flex.
- Next measured QA pass: fix `stale_location`/`not_in_story` (library book remains
  at library after delivery; added Ben/Ada locations), `misleading_sequence`
  (next indexed speech skips unindexed lines), `weak_causal_focus` (Why answers
  an earlier move's guard instead of current possession), and `wrong_speech_event`
  (observation quote attached to following Tell action). Keep this 100-sample
  worksheet frozen for comparison. Audit judge location hierarchy errors first:
  "in Mira's hands" and "at the porch" are compatible, not contradictions.
- Added exact quoted speech, speaker/listener questions, speech navigation,
  explicit reply links and reasons tied to the speaker's belief/goal. Optional
  claim annotations preserve truth-vs-assertion and before/after timing.
  The renderer indexes explicit names before bridge joining without extra model
  tokens; older frozen stories use the same conservative importer at QA time.
- Pin six dialogue cases separately from the six original trace-only pins.
  `unattributed_dialogue`: pronoun-only and unsupported interrupted attributions
  remain unindexed; do not mistake the next indexed quote for the next actual
  line of dialogue. `unrecorded_motive`: Tell context is not a stated motive.
  `unverified_speech_annotation`: exact spans and fact checks do not certify the
  author's semantic claim/reason mapping. Next gate: annotate a representative
  small world set, review speech/prose/state together, and measure reply/motive
  coverage alongside false attribution and stale-claim failures.
- Dialogue trial: `improvements/dialogue_qa_v1/REPORT.md`; no paid generation or
  semantic judge calls were made and the story prose benchmark is preserved.
- Added offline question/answer conversations with entity, event and time focus;
  follow-up source/why/next/previous/holder/location questions; belief-vs-truth
  checks; and explicit abstention for unknown motives and unsupported questions.
- Preserve original stories, traces, authoring prompts and old audit QA. New
  `--qa` output and chat export are optional; no runtime or authoring API cost
  is added. See `CONVERSATIONAL_QA.md`.
- Pin six cases across compact and older worlds, plus behavioral tests for
  stale belief transmission, loan return history, unsupported summary claims,
  ambiguous references and causal sibling effects. Keep the six-story smoke
  gate on question diversity, multi-turn continuity and full-sentence answers.
- `story_trace_mismatch`: some recorded locations disagree with English travel.
  QA export remains a review artifact until semantic answerability is verified
  against both story and trace. Do not hide the issue by inventing movement.
- `unsupported_fact_realization`: arbitrary local enums and non-entity legacy
  locations are still outside the typed QA vocabulary. Report coverage and
  underfilled conversations rather than silently fabricating answers.
- `repetitive_answer`, `too_shallow`: generic ownership/position questions can
  restate facts. Broaden useful causal explanations and author-time grammatical
  fact mappings before treating deterministic checks as literary acceptance.
- Trial evidence: `improvements/conversational_qa_v1/REPORT.md`. The older
  general goal of richer QA is now partly implemented; unrestricted questions,
  semantic alignment scoring and nuanced lessons remain future work.

## Cache pass — preserve the 7.75 quality benchmark

- Default `--cost-profile cache-only` preserves authoring/evaluation request
  content and settings, disabling one-use implicit cache writes. Complete
  authoring request equivalence is tested against legacy. The original world
  contract and frozen benchmark generators remain unchanged.
- Keep prefix/contract changes in the explicit `cached` experiment and prose
  factoring behind `--prose-layout factored`. Frozen-world comparisons scored
  6.65 and 7.50/9; a full-context repeat scored 7.30. None clears the user's
  7.75 target, so do not promote these outputs based on lower cost.
- Cross-world prefix reuse is now measured, with cached reads/writes separated
  from ordinary input. The SDK adapter preserves canonical saved HTTP bodies.
  Flex is required; authoring remains Luna, evaluation Terra. Include rejected
  drafts and repairs in cost per completed/accepted world.
- Batch known structural diagnostics before a paid repair. Named null patches
  can remove a mistaken reserved definition. Count completed loan/return state
  changes from executed history even when initial and final ownership agree.
  These checks do not invent facts or weaken diversity/causality requirements.
- Next gate: repeat a larger predeclared matched-quality comparison, with
  `unsupported_wish`, `weather_drift`, `carrier_location_drift`,
  `unrecorded_action` and `event_log_prose` measured alongside mean quality.
  Do not treat one 20-story 7.75 pilot as a guaranteed production mean, and do
  not repeatedly regenerate until an isolated favorable grade appears.
- Detailed trials, costs and manual readings:
  `improvements/cache_optimization_v1/REPORT.md` and `manual_review.md`.
- Final fresh trial: 8/10 generated, 800 saved/80 judged stories, 7.1875/9
  overall; matching baseline theaters score 7.95. Seven worlds pass fresh-seed
  replay. Bakery has `uncovered_ending_condition`; expand validated evidence
  coverage before authoring/acceptance rather than removing factual guards.
  Clocktower's 4.90 mean exposes `signal_count_mismatch`: narrated taps must
  follow the corrected bell state. All failures stay in quality/cost totals.
  Returned usage is $0.149336 plus a $0.020002 unknown-outcome reservation.
  Broad quality/holdout gates remain unmet, so keep prompt changes experimental.

## Compact algebra pass

- Implemented immutable role-bound kernels, pattern addition and attention
  division, automatic knowledge/loan slots, named component repairs, executable
  world JSON and trace-derived prose slots. See `COMPACT.md`.
- Group ending text by declared outcomes, passing only common evidence facts;
  guard every supplied fact. Default to one wording per slot. The initial
  roof-post trial shrank from 116 requested texts to 40 without changing its
  mechanics. This is library scaffolding, not shortened creative prose.
- Matched trial including failed drafts and all suffix recovery attempts:
  27,671 -> 20,773 output tokens (24.93% fewer); 18 -> 13 authoring requests.
  Both protocols completed 2/3 worlds. On the same two completed worlds, the
  unchanged judge's overall mean was 6.75 -> 7.75/9, diversity 3 -> 3.5/9.
- Keep `insufficient_output_budget` and `unreachable_goal` visible: roof-post
  remains quarantined after capped output, a 575-token continuation and six small
  patches. No full-script/stronger-model recovery. The capped response and every
  patch remain in the token totals. An earlier compiler-development run and the
  disk-interrupted control are reported separately, including reservations.
- `carrier_location_drift`: Move changes object location only. Add an explicit
  carrying primitive with co-location prerequisites and atomic actor/object
  movement; sample it against the compact pond-concert seed 1000 before claiming
  physically grounded carrying. Do not silently change saved Move semantics.
- `premature_accomplishment`, `event_log_prose`: the concert may precede its
  invitation; delivery confirmation is narrated as ledger state. Require causal
  prerequisites and narrative turns where the premise promises them.
- `incidental_outcome_diversity`: pad_secured can split an outcome signature
  without creating a new plot. Continue reporting semantic plot-group/diversity
  judgments separately from scalar state and permutation counts.
- Report and direct readings: `improvements/compact_v1/REPORT.md` and
  `manual_review.md`. The next scaling gate is a larger matched trial with these
  recurring physical and causal defects measured explicitly.

## Completed in the first improvement campaign

- Preserve the original 10-world run, all 320 hashed artifacts, and 30 replay pins.
- Review exact judged inputs using zero-based sample IDs; compare text and traces.
- Add keyword scene authoring, consistent shared-kernel arguments, safe state-key
  renames, and bounded atomic source/catalog patches. No implicit Terra recovery.
- Use Luna for authoring and repairs, Flex only, bounded outputs, per-world limits
  and one persistent campaign ledger. Separate generation and QA cost, including
  inherited and failed drafts in the 20,000-world projection.
- Prune irrelevant actions, replay retained paths, preserve invariant dependencies
  and pivotal character turns, and report scene sets/outcomes separately from
  ordered permutations.
- Detect intended outcomes that never occur because the goal stops too early.
- Render conditional prose from a data catalog with an explicit phrase lexicon,
  before/after fact bindings, grouped bridge cards, and deterministic lint.
- Report multiple failed seed combinations together when repairing prose coverage.
- Sample semantic critics across distinct outcomes, instead of using three seeds
  all divisible by three. Bound Terra diagnostics to 1,600 output tokens and
  three issues; critics receive stories/trace changes, never scripts.
- Freeze execution modules per run so later improvements cannot alter its samples.

## Training export dry run (2026-09-09)

- Added [the training adapter](EXPORTING.md) without changing generators, the
  older exporter, or the trainer. All 100 accepted worlds replayed at their 100
  saved seeds; all 300 graded story/conversation samples reproduced exactly.
  Physical state/evidence remains in source sidecars and drives the existing
  offline QA; no LLMs run during sampling or export.
- 10,000 samples deduplicate to **8,014 stories**, packed into **17,573 rows**:
  15,941 train / 1,632 dev. Hold out the entire `hill_picnic` family (10 worlds).
  Candidate export: 15,801,982 serialized tokens; 12,241,945 supervised tokens.
  48,084 intact conversations / 140,944 QA pairs; no context or chain truncation.
- The existing finalizer and training loader validated every row with the
  production 16k tokenizer at 1,024 tokens, including every loss-mask position.
  No ID/message duplicates or train/dev story/world overlap. **130 tests pass**.
- `judge_screened` exports contain 284 distinct stories in 392 rows and 916
  conversations, using only exact saved grades (story overall >=6; QA usable).
  This is candidate screening, not certified acceptance. API cost for export: $0.
- Before scaling: address `not_in_story`, `missing_causality`, `wrong_focus`,
  `ownership_drift` and `unrecorded_action`. Existing judge usability is only
  967/1,800 (53.7%); the other 58,200 newly materialized conversations are ungraded.
  Do not transfer a world's sampled grades to all of its seeds.
- Branch starting-condition prompts are now implemented and audited across all
  10,000 samples, with no distinct initial branches collapsing to the same
  prompt within a world. Facts are checked against initial state; unsupported
  values fail explicitly. Two complete example pairs are pinned under
  `examples/branch_prompts_v1/`. The historical export retains generic prompts.
  Add paraphrases and measure semantic prompt adherence, especially when
  numerical trait magnitudes are expressed qualitatively.
  Establish near-duplicate/plot screening across themes and the older corpus.
- Set task weights before production mixing: full packing repeats story
  supervision **2.19×**, with answers **24.6%** of assistant tokens. Decide the
  desired final-mixture allocation rather than equating rows with fresh stories.
- Preserve `training/storyworld_chat/data/storyscenes_100_20260909/split.json`
  for descendant batches. Report, manifests, decisions, traces, and exact token
  counts are saved alongside it. No 1,000-world authoring run has been started.

## Remaining defects and next measurable gates

- `unrecorded_action`, `ownership_drift`: a valid conditional card can still claim
  an unsupported extra action. Require claimed state changes/participants in
  future catalog schemas; evaluate English entailment separately. The current
  fact bindings are not a proof. Pin a traded-key display, a nonexistent ringing
  bell, and a banner used without attachment as semantic regression examples.
- `weak_turn`, `instructional_voice`, `duplicated_ending`: prefer consequential
  character decisions and one closing image to inspection sequences and repeated
  last-event summaries. Use blinded semantic comparisons; do not reward a weaker
  text merely because it has more trace keys.
- `unresolved_alternative`: lint covers known literal patterns, but phrases such
  as “under leaves or near the gate” can still leak alternatives. Guard openings
  on actual state; use semantic checks before expanding regex bans broadly.
- `unreachable_goal`: improve solver counterexamples to explain several failing
  initial configurations and their blocked prerequisites at once. Luna repairs
  sometimes fix one seed while breaking another. Do not relax invariants simply
  to obtain a green run.
- `unembedded_state`: prevent plans from introducing unattached abstract slots
  like performed.mode; use a physical performer/prop as carrier. Do not paper
  over the error by inventing a physical “event” entity.
- Measure *literary acceptance*, not just mechanically successful worlds. The
  cost per 20,000 usable worlds must include rejected drafts, failed API outcomes,
  and the chosen semantic review policy. A ten-world extrapolation is provisional.
- Compare an unassisted Luna batch and a bounded-critic batch on the same frozen
  generators, preserving both scores. Do not claim optional critic-guided quality
  is achieved for the price of unreviewed authoring alone.
- Distill useful shared scene kernels from storyscripts and test each in multiple
  theaters, with removal/replacement changing actual state outcomes. The current
  shared Observe/Tell/Transfer kernels are only a starting interface.
- Add a matched one-stage control (same briefs, model, budget and judge) before
  claiming the staged design improves on direct world/script generation.
- Extend mechanical QA into natural grounded answers and follow-ups. Keep belief
  state distinct from truth, and use world traces rather than free-text guessing.

## Final measured result (improvement_luna_v6)

- 10 completed worlds, 1,000 saved stories, 100 judged stories, 1,000 fresh
  offline samples, 30 pinned replays. Overall 6.94/9 versus 6.68; diversity
  3.20 versus 2.20; six stories below six versus seventeen. Storytelling fell
  6.80 → 6.61. Preserve the roof and hill regressions as well as the gains.
- 104 Luna authoring requests, 125,608 output tokens, approximately $0.1955,
  including failed/superseded inherited drafts. Bounded review + set evaluation
  adds $0.1922. All returned requests were Flex. Linear projections: about $391
  for authoring 20,000 mechanically successful worlds, or $775 including the
  same review/evaluation policy; this is not an acceptance-rate estimate.
- `wrong_patch_target`: a valid indexed patch changed roof_post's ribbon card
  into another hook-selection passage. Next gate: stable scene IDs + expected
  old text and event-alignment validation for every changed paragraph. Pin this
  regression before trusting automated literary repair at scale.
- The bounded critic sometimes treats narrator knowledge as character knowledge,
  or proposes unsupported new events. Keep review findings advisory and audit
  the *final* text against state. Do not count a proposed fix as a resolved issue.
