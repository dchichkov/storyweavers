"""Mental, social, communicative and narrative hypotheses, IDs 769--1024.

Examples are invented causal prefixes. A semantic projection is evidence about
an interpretation: it does not commit a physical event or erase alternatives.
"""

import re

from ..schema import Catalog, example, gap, neuron, present, ref, seq, tok


SOURCES = ("local.storyformer", "local.memeplex", "circuits.binding", "circuits.biology",
           "sae.absorption", "sae.autointerp")


def _context(text, *, holder="e1"):
    """Word/punctuation adapter convention, with a declared example scope."""
    result = []
    for token in re.findall(r"\w+(?:['’]\w+)?|[^\w\s]", text):
        record = {"token": token, "scope_id": "s1", "assertion_status": "asserted"}
        if token == "Mia":
            record.update(entity_id=holder, entity_name="Mia", pos="n")
        elif token == "Ben":
            record.update(entity_id="e2", entity_name="Ben", pos="n")
        result.append(record)
    return result


def _cue(cat, family, holder_key, lemma, surface, event_type, rows):
    """Four finite construction seeds; correlated emission needs an adapter."""
    coarse_type = {"mental_attitude": "state", "intention": "state", "affective_attitude": "feel",
                   "social_attitude": "state", "communication": "speak", "discourse_comparison": "other",
                   "reasoning": "state", "perception": "perceive"}[event_type]
    pattern = seq(gap(), tok(bind="person", entity_id=present(), scope_id=present()),
                  tok(bind="cue", pos="v", lemma=lemma, event_type=coarse_type,
                      scope_id=ref("person.scope_id"), event_id=present()))
    context = [dict(token="Mia", pos="n", entity_id="e1", scope_id="s1", assertion_status="asserted"),
               dict(token=surface, pos="v", lemma=lemma, event_type=coarse_type,
                    event_id="ev2", scope_id="s1", assertion_status="asserted")]
    negative = [dict(context[0]), {**context[1], "pos": "n", "event_type": "other"}]
    for key, kind, description, value, projection in rows:
        if key.endswith("_scope_bundle"):
            value = {**value, "assertion_status": "candidate"}
            projection = {**projection, "assertion_status": "candidate"}
        emit = {holder_key: ref("person.entity_id"), key: projection,
                "event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id"), "assertion_status": "candidate"}
        expected = {holder_key: "e1", key: value, "event_id": "ev2", "scope_id": "s1", "assertion_status": "candidate"}
        cat.add(key, kind, description, family, value=value,
                scope=f"Current {event_type} construction, bound through {holder_key} and scope_id.",
                head=f"propose_{key}_from_{lemma}_construction",
                function=f"Project a provisional {key} from an adjacent entity and an annotated {lemma} verb; leave its content unresolved.",
                mechanism="bounded_construction_capture_and_typed_projection",
                positive=example(context, expected, f"The visible finite construction licenses this {key} candidate; no complement or later text is used."),
                negative=example(negative, {}, f"The same surface is a quoted noun mention, so the {lemma} event construction is absent."),
                native=neuron(pattern, emit), writes=list(emit), sources=SOURCES,
                notes="Requires a previously annotated verb sense. This is a candidate frame projection, not a lexical assertion about a character's mind. A following complement may refine or reject it.",
                intervention=f"Change the verb to a quoted mention or swap the preceding entity ID; {key} must abstain or track the new holder without changing another entity.")


def _carry(cat, family, holder_key, rows):
    """Retrieve earlier evidence for a new mention of the same scoped holder."""
    for key, kind, description, value in rows:
        pattern = seq(gap(), tok(bind="prior", **{holder_key: present(), key: present(), "event_id": present(),
                                                  "scope_id": present(), "assertion_status": "asserted"}),
                      gap(), tok(bind="mention", entity_id=ref(f"prior.{holder_key}"),
                                 scope_id=ref("prior.scope_id")))
        emit = {key: ref(f"prior.{key}"), holder_key: ref(f"prior.{holder_key}"), "event_id": ref("prior.event_id"),
                "scope_id": ref("prior.scope_id"), "assertion_status": "candidate"}
        context = [dict(token="earlier", **{holder_key: "e1", key: value, "event_id": "ev_prior",
                                            "scope_id": "s1", "assertion_status": "asserted"}),
                   dict(token="Mia", entity_id="e1", scope_id="s1", assertion_status="asserted")]
        expected = {key: value, holder_key: "e1", "event_id": "ev_prior", "scope_id": "s1", "assertion_status": "candidate"}
        negative = [context[0], {**context[1], "entity_id": "e2"}]
        cat.add(key, kind, description, family, value=value,
                scope=f"Scoped evidence about {holder_key}; retrieved at a later co-referential mention.",
                head=f"retrieve_scoped_{key}",
                function=f"Copy an earlier supported {key} into the current mention's hypothesis while retaining holder and scope.",
                mechanism="entity_keyed_scoped_evidence_copy",
                positive=example(context, expected, "The source is earlier evidence and the new mention has the same entity ID and scope."),
                negative=example(negative, {}, "A distractor shares the visible name but has a different identity, so this holder-specific retrieval cannot fire."),
                native=neuron(pattern, emit), writes=list(emit), sources=SOURCES,
                notes="Carries an event-anchored hypothesis; it does not assert that the value is still current or choose the latest source. The witness has one source. Multiple sources produce derivations, but current fieldwise residual merging does not preserve joint tuples; correlated multi-source use needs a bundle adapter. Freshness/revision needs a separate head.",
                intervention=f"Swap only the current entity or scope; {key} must not cross that boundary. Add a contradictory source to inspect preserved alternatives.")


def _group(cat, family, holder_key, label, positive_text, negative_text, predicate, contrast,
           rows, *, requires=("proposition_binding", "scope_resolution"), holders=None,
           mechanism="scoped_semantic_relation_projection"):
    """Four independently typed dimensions of a specified semantic operation.

    The contract consumes a parsed proposition graph over visible spans, which
    the current finite-pattern engine does not supply. It never calls an LLM.
    """
    holders = holders or {holder_key: "e1"}
    for row in rows:
        key, kind, description, value, *overrides = row
        row_holders = overrides[0] if overrides else holders
        emit = {**row_holders, key: value, "scope_id": "s1", "assertion_status": "candidate"}
        contract = {
            "match": {
                "binders": {
                    "holder": {"entity_id": "from explicit participant binding", "role": holder_key},
                    "scope": {"id": "scope containing the evidence", "allowed": "visible prefix only"},
                    "evidence": {"relation": label, "predicate": predicate,
                                 "support": "explicit spans or previously derived scoped propositions"},
                },
                "query": "current final token in the same discourse scope",
                "select": f"The {key} dimension of the matched {label} evidence; preserve other readings as alternatives.",
            },
            "guards": [
                "Resolve participant identity; a matching name string alone is insufficient.",
                "Every source position is at or before the query.",
                "Keep quotation, belief, hypothetical and narrator assertion scopes distinct.",
                "Unknown or contradicted prerequisites produce no projection, not a false value.",
                contrast,
            ],
            "emit": {
                key: {"derive": description, "from": ["evidence", "holder", "scope"],
                      "example_value": value},
                **{name: {"copy_binding": name} for name in row_holders if name != key},
                "scope_id": {"copy_binding": "scope.id"},
                "assertion_status": "candidate",
            },
            "effect": "Add evidence for a typed interpretation at the current query; do not commit world state.",
            "ambiguity": "If multiple compatible bindings exist, retain separately scoped alternatives rather than merging their fields.",
        }
        cat.add(key, kind, description, family, value=value,
                scope=f"{label}; holder/participants are {', '.join(row_holders)} with a proposition and scope anchor.",
                head=f"derive_{key}_from_{label}",
                function=f"Resolve {label} evidence and project its {key} dimension: {description}",
                mechanism=mechanism,
                positive=example(_context(positive_text), emit, predicate),
                negative=example(_context(negative_text), {}, contrast),
                contract=contract, requires=requires,
                reads=["token", "entity_id", "scope_id", "assertion_status", "event_id", "attributes", *row_holders],
                writes=list(emit), sources=SOURCES,
                notes="Adapter contract, not a grammar accepted by parse_neuron. Values shown are a causal witness; an implementation must bind content/participants from the prefix, not emit these example constants for other stories.",
                intervention=f"Hold wording constant where possible while changing the holder, scope, or {label} prerequisite; verify selective change in {key} and preserved unrelated bindings.")


def _epistemic(c):
    f, h = "epistemic_attitude", "belief_holder_id"
    _cue(c, f, h, "believe", "believes", "mental_attitude", [
        (h, "entity_ref", "Entity to whom the current belief candidate is attributed; this is not a narrator truth claim.", "e1", ref("person.entity_id")),
        ("epistemic_attitude_kind", "string", "Kind of propositional attitude currently proposed, such as belief, doubt, or knowledge claim.", "belief", "belief"),
        ("epistemic_content_binding_status", "string", "Incremental status of binding a content proposition to the attitude; pending_complement is a parse state, not a mental fact.", "pending_complement", "pending_complement"),
        ("epistemic_scope_bundle", "object", "Correlated holder, attitude-event, and discourse-scope binding for an epistemic interpretation.",
         {"holder_id": "e1", "attitude_event_id": "ev2", "scope_id": "s1"},
         {"holder_id": ref("person.entity_id"), "attitude_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("belief_content_id", "string", "Proposition ID of what this holder believes, preserving the proposition's own polarity and arguments.", "p_open_gate"),
        ("belief_polarity", "string", "Whether the holder accepts or rejects the bound proposition, separately from its grammatical negation.", "accepts"),
        ("belief_certainty", "string", "Reported certainty of the holder about the bound belief, not model confidence.", "tentative"),
        ("epistemic_source_kind", "string", "Holder-attributed source category for the belief, such as perception, testimony, inference, or memory.", "testimony"),
    ])
    _group(c, f, h, "knowledge_claim", "Mia says she knows the gate is open because she saw it.",
           "Mia says she guesses the gate is open but has not seen it.",
           "An explicit knowledge claim binds its holder, content and claimed perceptual access without proving the content true.",
           "A guess with denied access does not license the knowledge-claim witness.", [
        ("knowledge_claim_holder_id", "entity_ref", "Entity presented as knowing the content in an explicit knowledge claim.", "e1"),
        ("knowledge_claim_content_id", "string", "Proposition ID claimed to be known; factivity remains separately scoped.", "p_open_gate"),
        ("epistemic_access_mode", "string", "Claimed mode of access supporting this epistemic attitude.", "visual_perception"),
        ("epistemic_evidence_strength", "string", "Text-supported qualitative strength of the holder's cited evidence, distinct from certainty.", "direct_observation_claimed"),
    ])
    _group(c, f, h, "explicit_doubt", "Mia doubts Ben's claim that the gate is open and asks whether it is shut.",
           "Mia repeats Ben's claim that the gate is open without expressing doubt.",
           "A doubt predicate and alternative question explicitly place one proposition under uncertainty for the holder.",
           "Repeating a claim alone does not establish doubt or an alternative under consideration.", [
        ("doubt_holder_id", "entity_ref", "Entity explicitly expressing doubt toward a proposition.", "e1"),
        ("doubt_content_id", "string", "Proposition targeted by doubt rather than an unrelated topic.", "p_open_gate"),
        ("epistemic_alternatives", "array", "Explicitly considered alternative proposition IDs within the holder's uncertainty.", ["p_open_gate", "p_shut_gate"]),
        ("epistemic_question_under_discussion", "string", "Question ID whose answer would resolve the holder's currently stated uncertainty.", "q_gate_state"),
    ])
    _group(c, f, h, "belief_update", "Mia first thought the gate was open. Seeing that it had been shut all along, she says she was wrong and changes her mind.",
           "Mia thought the gate was open. Ben saw it shut but did not tell her.",
           "The same holder receives contrary evidence and explicitly revises the earlier belief.",
           "Evidence available only to another character cannot revise this holder's belief.", [
        ("belief_revision", "object", "Directed revision from an earlier belief to a newly adopted content with its evidence event.", {"old": "p_open_gate", "new": "p_shut_gate", "basis": "ev_seeing"}),
        ("belief_error_status", "string", "Whether an earlier belief is contradicted by available narrator-supported evidence; does not mean the holder already knows.", "contradicted_in_prefix"),
        ("epistemic_resolution_status", "string", "Status of a previously open epistemic issue for the holder.", "resolved_by_observation"),
        ("epistemic_time_scope", "object", "Time interval or event-relative phase in which a particular attitude is attributed.", {"belief": "p_open_gate", "phase": "before_ev_seeing"}),
    ], requires=("proposition_binding", "scope_resolution", "attitude_revision_graph"), mechanism="holder_specific_belief_revision")
    _group(c, f, h, "nested_attitude", "Mia thinks Ben believes the gate is open; she says she has never checked it herself and does not know whether it is actually open.",
           "Mia and Ben stand by the gate; neither describes what the other believes.",
           "Explicit embedding establishes a belief about another holder's belief and a self-reported knowledge limitation.",
           "Co-presence does not imply mutual belief or knowledge of another mind.", [
        ("belief_nested_holders", "array", "Ordered holder IDs from outer attitude to embedded attitude; order is semantically significant.", ["e1", "e2"]),
        ("belief_about_own_knowledge", "object", "Holder's explicit metacognitive claim about their knowledge of a proposition.", {"holder_id": "e1", "content_id": "p_gate_state", "status": "not_checked"}),
        ("knowledge_gap_holder_id", "entity_ref", "Entity whose explicit knowledge gap is being represented.", "e1"),
        ("knowledge_gap_content_id", "string", "Question/proposition ID that the holder explicitly lacks sufficient knowledge to settle.", "q_gate_state"),
    ], requires=("nested_attitude_graph", "scope_resolution", "cross_clause_coreference"))
    _group(c, f, h, "disputed_testimony", "Mia trusts Ben on gates, but she rejects his claim that this gate is open; Ben still insists it is.",
           "Mia thanks Ben for pointing at the gate; no claim or disagreement is stated.",
           "A named source, explicit rejection and continuing contrary assertion define a scoped epistemic disagreement.",
           "Social courtesy or pointing alone supplies neither disputed content nor an acceptance decision.", [
        ("epistemic_source_entity_id", "entity_ref", "Entity credited as the source of the proposition under discussion.", "e2"),
        ("belief_acceptance_status", "string", "Holder's explicit uptake decision toward a received claim.", "rejected"),
        ("epistemic_disagreement_parties", "array", "Entities explicitly taking incompatible stances toward the same content.", ["e1", "e2"]),
        ("epistemic_disputed_content_id", "string", "Shared proposition ID whose acceptance differs between the parties.", "p_open_gate"),
    ])
    _group(c, f, h, "epistemic_alignment", "Mia and Ben both accept the caretaker's report, saying she knows the gate best; Mia says it agrees with her earlier belief about the gate.",
           "Mia and Ben hear the caretaker, but neither says whether they accept her report.",
           "Acceptance, attributed authority and agreement are separately evidenced in the same visible exchange.",
           "Hearing a report is not accepting it, sharing a belief, or endorsing its source's authority.", [
        ("belief_shared_with", "array", "Other entities with explicit evidence of accepting the same scoped proposition.", ["e2"]),
        ("belief_consistency", "string", "Compatibility of the holder's explicitly represented beliefs in the examined scope.", "consistent_on_stated_issue"),
        ("epistemic_authority_attribution", "object", "Holder's attribution of domain expertise to a source, not objective proof of expertise.", {"holder_id": "e1", "source_id": "e3", "domain": "gate_condition"}),
        ("epistemic_attitude_target", "object", "Correlated proposition, issue and contextual referent that an attitude is about.", {"content_id": "p_gate_report", "issue_id": "q_gate_state", "referent_id": "e4"}),
    ])


def _goals(c):
    f, h = "goals_intentions", "goal_owner_id"
    _cue(c, f, h, "intend", "intends", "intention", [
        (h, "entity_ref", "Entity whose goal or intended state is being represented.", "e1", ref("person.entity_id")),
        ("intention_holder_id", "entity_ref", "Entity explicitly taking the intention attitude; can differ from a goal beneficiary.", "e1", ref("person.entity_id")),
        ("goal_status", "string", "Lifecycle status of a goal hypothesis; proposed means a goal cue is visible but its content is not yet resolved.", "proposed", "proposed"),
        ("goal_scope_bundle", "object", "Correlated owner, intention-event and scope binding for a goal interpretation.",
         {"owner_id": "e1", "intention_event_id": "ev2", "scope_id": "s1"},
         {"owner_id": ref("person.entity_id"), "intention_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("goal_content_id", "string", "Proposition or desired-state ID that defines the owner's goal.", "p_repaired_kite"),
        ("goal_polarity", "string", "Whether the goal seeks the bound state or seeks to avoid it.", "achieve"),
        ("intention_content_id", "string", "Action/proposition ID explicitly intended by the holder.", "p_repair_kite"),
        ("intention_strength", "string", "Text-supported commitment degree of an intention, separate from feasibility.", "firm"),
    ])
    _group(c, f, h, "goal_criteria", "Mia puts repairing the kite ahead of making a toy. She wants it repaired by sunset; it must fly without tearing, and another tear would mean failure.",
           "Mia looks at the torn kite at sunset without stating a goal or success criterion.",
           "An explicit desired state includes a deadline and distinct success/failure tests.",
           "An object state and a time mention do not supply a goal criterion.", [
        ("goal_deadline", "object", "Explicit temporal bound for achieving a goal, anchored to the owner's plan.", {"anchor": "sunset", "relation": "by"}),
        ("goal_success_condition", "string", "Proposition that would count as success under the stated goal criterion.", "p_kite_flies_without_tearing"),
        ("goal_failure_condition", "string", "Proposition explicitly identified as failure for this goal.", "p_kite_tears_again"),
        ("goal_priority", "string", "Owner's stated ordering or importance of the goal relative to other explicitly considered goals.", "above_toy_making"),
    ])
    _group(c, f, h, "goal_decomposition", "To repair the kite, Mia plans first to find thread and then to sew the tear.",
           "Mia mentions thread, sewing, and a kite without saying they form a plan.",
           "A purpose construction and ordered plan explicitly relate subgoals and steps to the repair goal.",
           "Co-occurring actions do not establish a plan hierarchy or next step.", [
        ("goal_parent_id", "string", "ID of the higher-level goal served by the current subgoal.", "g_repair_kite"),
        ("goal_subgoal_ids", "array", "Explicitly related lower-level goals needed or chosen for the parent goal.", ["g_find_thread", "g_sew_tear"]),
        ("plan_step_ids", "array", "Ordered action IDs in an explicitly represented plan.", ["a_find_thread", "a_sew_tear"]),
        ("plan_next_step_id", "string", "Next pending action according to the stated plan and visible completion record.", "a_find_thread"),
    ], requires=("goal_plan_graph", "scope_resolution", "ordered_step_selection"))
    _group(c, f, h, "goal_dependencies", "Mia wants to repair Ben's kite because she wants to help him, but she says missing thread blocks her and she needs a needle.",
           "Mia sees thread and a needle near Ben's kite without stating a goal or need.",
           "The holder explicitly ties an obstacle, resource and beneficiary to a repair goal.",
           "Nearby objects are not automatically required resources or obstacles.", [
        ("goal_obstacle_ids", "array", "State/event IDs explicitly impeding the bound goal, from the owner's perspective.", ["p_thread_missing"]),
        ("goal_resource_ids", "array", "Entity or resource IDs explicitly needed or allocated to the goal.", ["e3"]),
        ("goal_beneficiary_ids", "array", "Entities explicitly intended to benefit from the goal's success.", ["e2"]),
        ("goal_motivation", "object", "Stated reason for pursuing the goal, with holder and beneficiary preserved.", {"reason": "help_with_kite", "beneficiary_id": "e2"}),
    ])
    _group(c, f, h, "goal_tradeoff", "Mia tells Ben she intends to finish before sunset and keep the kite strong; she chooses strength even if it takes longer.",
           "Mia says sunset is beautiful and the kite is strong, without choosing between goals.",
           "The text names two potentially conflicting goals and an explicit preference under conflict.",
           "Independent descriptions do not establish a tradeoff or feasibility judgment.", [
        ("goal_conflict_ids", "array", "Goal IDs whose simultaneously satisfying demands are explicitly presented as conflicting.", ["g_finish_by_sunset", "g_keep_strength"]),
        ("goal_tradeoff", "object", "Owner's explicit preference or concession when balancing goals.", {"prefer": "g_keep_strength", "relax": "g_finish_by_sunset"}),
        ("goal_feasibility_judgment", "string", "Owner's expressed assessment of whether the goal can be achieved under stated constraints.", "timely_completion_uncertain"),
        ("intention_publicity", "string", "Whether the intention is explicitly communicated, privately attributed, or unknown.", "communicated"),
    ])
    _group(c, f, h, "contingent_plan_revision", "Mia had planned to sew the kite. She now promises to patch it instead, using cloth if thread cannot be found.",
           "Mia lists sewing, patching, cloth and thread as words on a page.",
           "A prior plan, replacement commitment and conditional fallback are explicitly connected.",
           "A lexical list has no intention, replacement relation or contingency.", [
        ("plan_contingency", "object", "Condition-action branch explicitly attached to a plan.", {"if": "p_thread_unavailable", "then": "a_use_cloth"}),
        ("plan_commitment_status", "string", "Whether a plan is tentative, adopted, promised, suspended, or abandoned according to visible evidence.", "promised"),
        ("plan_revision", "object", "Explicit replacement or alteration of a prior plan component.", {"replace": "a_sew_kite", "with": "a_patch_kite"}),
        ("goal_adoption_event_id", "string", "Event that explicitly marks adoption or commitment to the current goal/plan.", "ev_promise_patch"),
    ], requires=("goal_plan_graph", "scope_resolution", "conditional_branch_binding"))
    _group(c, f, h, "goal_closure", "Mia says the kite now flies as she wanted. She stops repairing it, satisfied that her work matched her plan.",
           "Mia dreams that the kite flies; she wakes to find the repair unfinished.",
           "A real-scope outcome is compared with the stated criterion and the owner explicitly closes the goal.",
           "Dreamed success does not complete a waking goal or establish satisfaction after completion.", [
        ("goal_progress_judgment", "string", "Owner-attributed assessment of progress toward the explicit success criterion.", "complete"),
        ("goal_satisfaction_judgment", "string", "Owner's expressed evaluation of how well the result satisfies the goal.", "satisfied"),
        ("intention_vs_action_alignment", "object", "Comparison between an earlier intention and a visible action/outcome under the same goal.", {"intention": "p_repair_kite", "outcome": "p_kite_flies", "alignment": "fulfilled"}),
        ("goal_termination_event_id", "string", "Event marking cessation of pursuit; the reason distinguishes satisfied closure from frustrated abandonment.", "ev_stop_after_success"),
    ], requires=("goal_plan_graph", "scope_resolution", "goal_criterion_comparison"))


def _affect(c):
    f, h = "affect_appraisal", "affect_experiencer_id"
    _cue(c, f, h, "fear", "fears", "affective_attitude", [
        (h, "entity_ref", "Entity to whom an affective state is attributed.", "e1", ref("person.entity_id")),
        ("affect_kind", "string", "Named affect category supported by the current attribution; it is not an immutable character trait.", "fear", "fear"),
        ("affect_expression_channel", "string", "Evidence channel through which affect is attributed, rather than an assumed behavioral symptom.", "explicit_predicate", "explicit_predicate"),
        ("affect_scope_bundle", "object", "Correlated experiencer, affect event and assertion scope for the current affect hypothesis.",
         {"experiencer_id": "e1", "affect_event_id": "ev2", "scope_id": "s1"},
         {"experiencer_id": ref("person.entity_id"), "affect_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("affect_target_id", "string", "Entity, event or proposition ID toward which this affect is directed.", "p_storm_arriving"),
        ("affect_valence", "string", "Explicitly supported pleasant/unpleasant/mixed evaluation of the experience, separate from social approval.", "unpleasant"),
        ("affect_arousal", "string", "Text-supported level of activation or calmness of the affective experience.", "high"),
        ("affect_intensity", "string", "Explicitly supported strength of the attributed affect; no numeric strength is invented from a label.", "mild"),
    ])
    _group(c, f, h, "affect_self_and_other", "Mia says she was terrified but now feels only uneasy and pretends to be calm; Ben calls her still terrified, but she says that is too strong.",
           "Mia reads the words uneasy and terrified from a dictionary.",
           "Different attributed sources describe the same experiencer and explicitly disagree about degree.",
           "Mentioning emotion words is not experiencing or attributing the emotions.", [
        ("affect_self_report", "object", "Experiencer's own expressed affect description with source and content preserved.", {"source_id": "e1", "kind": "unease"}),
        ("affect_observer_attribution", "object", "Another entity's affect attribution, which may disagree with the experiencer.", {"source_id": "e2", "kind": "terror", "accepted_by_experiencer": False}),
        ("affect_display_authenticity", "string", "Explicit evidence about whether an outward display matches the experienced affect; unknown unless addressed.", "deliberately_mismatched"),
        ("affect_change", "object", "Explicitly reported change in the experiencer's affect, retaining its attributed source.", {"source_id": "e1", "from": "terror", "to": "unease"}),
    ])
    _group(c, f, h, "mixed_affect", "Mia says she is glad Ben is safe and sad the kite is lost; she has felt both since noon.",
           "Mia says Ben is glad and another child is sad, without reporting her own feelings.",
           "One experiencer explicitly reports concurrent affects with distinct targets and a shared onset.",
           "Emotions belonging to different entities cannot be merged into this experiencer's mixed affect.", [
        ("affect_mixed_components", "array", "Coexisting affect components, each retaining kind and target instead of averaging them away.", [{"kind": "gladness", "target": "p_ben_safe"}, {"kind": "sadness", "target": "p_kite_lost"}]),
        ("affect_social_target_ids", "array", "Other entities explicitly involved as targets or beneficiaries of the affect.", ["e2"]),
        ("affect_duration", "object", "Text-stated temporal extent or onset of the affective state.", {"onset": "noon", "ongoing": True}),
        ("affect_cause_claim", "object", "Scoped causal explanation offered for affect, not an unqualified world causal assertion.", {"gladness": "p_ben_safe", "sadness": "p_kite_lost"}),
    ])
    _group(c, f, h, "goal_appraisal", "Mia says losing the thread matters because it blocks her repair goal; she did not expect it and has never faced this before.",
           "Mia notices thread on a shelf without evaluating its relevance or novelty.",
           "The experiencer explicitly evaluates relevance, goal compatibility, expectation and novelty of one event.",
           "An event mention alone does not fix any appraisal dimension.", [
        ("appraisal_goal_relevance", "string", "Experiencer's expressed degree or kind of relevance of an event to an active goal.", "directly_relevant"),
        ("appraisal_goal_congruence", "string", "Whether the experiencer evaluates the event as helping or obstructing the bound goal.", "obstructing"),
        ("appraisal_expectedness", "string", "Whether the experiencer explicitly anticipated the event.", "unexpected"),
        ("appraisal_novelty", "string", "Whether the experience is described as new or familiar to this experiencer.", "first_experience"),
    ])
    _group(c, f, h, "control_and_responsibility", "Mia says she caused the spill, can clean it, and is responsible for doing so; she calls that fair.",
           "Mia watches Ben clean a spill and makes no claim about cause, control or fairness.",
           "The holder makes separate agency, control, responsibility and fairness appraisals.",
           "Observing an action does not assign blame or control to the observer.", [
        ("appraisal_controllability", "string", "Experiencer's expressed ability to influence the relevant event or consequence.", "can_remedy"),
        ("appraisal_agency", "object", "Entity the experiencer attributes as causing or controlling the event.", {"agent_id": "e1", "event_id": "ev_spill"}),
        ("appraisal_responsibility", "object", "Experiencer-attributed responsibility, which is distinct from causal agency.", {"responsible_id": "e1", "for": "p_clean_spill"}),
        ("appraisal_fairness", "string", "Experiencer's explicit evaluation of fairness, not an objective normative verdict.", "fair"),
    ])
    _group(c, f, h, "coping_appraisal", "Mia says the leak is certain, must be fixed now, and is within her ability; asking for help would respect their rules.",
           "Mia hears the word leak in a game and states no judgment about urgency or ability.",
           "Explicit appraisal clauses address likelihood, urgency, coping resources and norm compatibility.",
           "A hazard word alone does not imply urgency, certainty or coping capacity.", [
        ("appraisal_certainty", "string", "Experiencer's stated certainty that the appraised event holds or will occur.", "certain"),
        ("appraisal_urgency", "string", "Experiencer's expressed need for immediate or delayed response.", "immediate"),
        ("appraisal_coping_capacity", "string", "Experiencer's assessment of resources or ability to manage the event.", "sufficient"),
        ("appraisal_norm_compatibility", "string", "Experiencer's evaluation of an action against an explicitly relevant norm.", "compatible"),
    ])
    _group(c, f, h, "affect_regulation", "Mia feels her stomach tighten and wants to run away, but deliberately takes slow breaths to calm herself and hides her worry from Ben.",
           "Mia runs for exercise and breathes slowly afterward; no worry or concealment is stated.",
           "The text links an embodied feeling, action tendency, deliberate regulation and concealment to an attributed affect.",
           "Running and breathing alone do not prove fear, regulation or masking.", [
        ("affect_embodied_sensation", "object", "Explicitly attributed bodily experience linked by the text to an affect.", {"sensation": "tightness", "site": "stomach"}),
        ("affect_action_tendency", "string", "Action the experiencer feels inclined toward, distinct from an action actually performed.", "run_away"),
        ("affect_regulation_strategy", "string", "Deliberate strategy explicitly used to alter or manage affect.", "slow_breathing"),
        ("affect_masking_status", "object", "Intentional concealment or display modulation of affect toward a specified audience.", {"status": "concealed", "audience_ids": ["e2"]}),
    ])


def _social(c):
    f, h = "social_relations", "trust_holder_id"
    _cue(c, f, h, "trust", "trusts", "social_attitude", [
        (h, "entity_ref", "Entity whose domain-specific trust attribution is represented.", "e1", ref("person.entity_id")),
        ("social_relation_kind", "string", "Kind of social relation proposed by an explicit relation construction.", "trust", "trust"),
        ("social_relation_status", "string", "Evidence status of a social relation; proposed does not mean permanently established.", "proposed", "proposed"),
        ("social_scope_bundle", "object", "Correlated social-attitude holder, event and assertion scope.",
         {"holder_id": "e1", "relation_event_id": "ev2", "scope_id": "s1"},
         {"holder_id": ref("person.entity_id"), "relation_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("trust_target_id", "entity_ref", "Entity trusted in the explicitly represented domain; trust is not necessarily reciprocal.", "e2"),
        ("trust_domain", "string", "Domain or action class to which a trust attribution applies.", "keeping_promises"),
        ("trust_level", "string", "Explicitly stated strength of trust; does not generalize to other domains.", "conditional"),
        ("social_relation_direction", "string", "Directionality of the represented social relation.", "holder_to_target"),
    ])
    _group(c, f, h, "obligation_assignment", "Mia promises Ben to return the needle tomorrow, and Ben accepts her promise.",
           "Ben asks Mia to return a needle, but she has not agreed or promised.",
           "An explicit accepted promise establishes a scoped commitment with debtor, creditor and content.",
           "A request alone does not license the accepted-obligation witness.", [
        ("obligation_debtor_id", "entity_ref", "Entity bound by the attributed obligation.", "e1"),
        ("obligation_creditor_id", "entity_ref", "Entity to whom the attributed obligation is owed.", "e2"),
        ("obligation_content_id", "string", "Action/proposition ID that constitutes the obligation's content.", "p_return_needle"),
        ("obligation_status", "string", "Lifecycle state of the attributed obligation under the visible evidence.", "accepted_commitment"),
    ], holders={"obligation_debtor_id": "e1", "obligation_creditor_id": "e2"})
    _group(c, f, h, "permission_grant", "Mia tells Ben he may borrow her needle for sewing; she says the permission lasts today.",
           "Ben wonders whether Mia might let him borrow her needle, without asking her.",
           "An explicit grant identifies grantor, recipient and limited permitted content.",
           "A hoped-for permission is not a grant from the named owner.", [
        ("permission_grantor_id", "entity_ref", "Entity explicitly granting the represented permission.", "e1"),
        ("permission_recipient_id", "entity_ref", "Entity to whom permission is granted.", "e2"),
        ("permission_content_id", "string", "Bound action ID permitted by the grant, preserving purpose and limits.", "p_borrow_needle_for_sewing_today"),
        ("permission_status", "string", "Current evidence-supported status of the permission, not entitlement inferred from desire.", "granted_limited"),
    ], holders={"permission_grantor_id": "e1", "permission_recipient_id": "e2"})
    _group(c, f, h, "social_rule_source", "Mia says the club chose her to lead repairs, so its rule makes her responsible for returning tools.",
           "Mia calls herself leader, but the club has neither appointed her nor stated any tool rule.",
           "A reported appointment and explicit rule ground a limited authority and obligation attribution.",
           "Self-description alone does not establish the stated institutional basis.", [
        ("obligation_source", "object", "Norm, agreement or event invoked as the basis of an obligation.", {"kind": "club_rule", "content": "return_shared_tools"}),
        ("social_power_basis", "string", "Explicitly attributed basis of influence or authority, rather than assumed dominance.", "delegated_role"),
        ("authority_scope", "object", "Actions, participants and domain over which an authority claim applies.", {"domain": "repairs", "group": "g_club"}),
        ("social_norm_claim", "object", "A norm attributed to a group/source, distinct from universal moral truth.", {"source": "g_club", "content": "return_shared_tools"}),
    ], holders={"obligation_debtor_id": "e1"})
    _group(c, f, h, "cooperation_and_conflict", "Mia and Ben join the repair club and agree to mend the kite together, though they disagree about who should keep it.",
           "Mia and Ben stand beside the club sign without joining, agreeing or discussing ownership.",
           "Joint commitment and a separate conflict issue coexist among explicitly bound participants.",
           "Co-location does not establish affiliation, cooperation or conflict.", [
        ("social_relation_participants", "object", "Participant bindings for a multi-party social relation, preserving roles.", {"members": ["e1", "e2"]}),
        ("cooperation_goal_id", "string", "Goal explicitly adopted as shared work by the participants.", "g_mend_kite"),
        ("cooperation_commitment", "string", "Status or strength of explicitly agreeing to act jointly.", "mutually_agreed"),
        ("conflict_issue_id", "string", "Proposition/question on which the participants explicitly conflict.", "q_kite_owner"),
    ], holders={"social_relation_participants": {"members": ["e1", "e2"]}})
    _group(c, f, h, "reciprocity_and_reputation", "Mia joins the repair club. Because Ben helped her, she says she owes him help; she calls him dependable.",
           "Mia sees Ben at the club but says nothing about membership, repayment or his reliability.",
           "Membership, reciprocal expectation and reputation are explicitly attributed rather than read from co-occurrence.",
           "Presence at a place does not establish group membership or social debt.", [
        ("affiliation_group_id", "string", "Group with which an entity explicitly affiliates or is reported to be a member.", "g_repair_club"),
        ("reciprocity_expectation", "object", "Explicit expectation of returning a benefit, with benefactor and intended response.", {"benefactor_id": "e2", "response": "help_in_return"}),
        ("social_debt_record", "object", "Attributed outstanding social debt, separate from legal or material ownership.", {"debtor_id": "e1", "creditor_id": "e2", "basis": "ev_prior_help"}),
        ("reputation_attribution", "object", "Trait/reputation judgment attributed to a source about another entity.", {"source_id": "e1", "target_id": "e2", "judgment": "dependable"}),
    ], holders={"trust_holder_id": "e1"})
    _group(c, f, h, "consent_and_boundary", "Mia tells Ben he may hold her hand today but not hug her; after he respects that, she says she trusts him more.",
           "Mia stays silent while Ben guesses what contact she might welcome.",
           "Explicit bounded consent, an excluded action and a later stated trust change are available in the prefix.",
           "Silence or a guess cannot establish consent or the experiencer's relational change.", [
        ("boundary_preference", "object", "Explicitly communicated personal boundary, anchored to its owner and excluded action.", {"owner_id": "e1", "excluded": "p_hug_mia"}),
        ("consent_status", "string", "Evidence-supported consent decision for the specified action; no inference from silence.", "explicit_limited_yes"),
        ("consent_scope", "object", "Participants, action and temporal limits of an explicit consent decision.", {"giver_id": "e1", "other_id": "e2", "action": "hold_hand", "time": "today"}),
        ("relationship_change", "object", "Explicitly attributed change in a social relation with cause claim preserved.", {"holder_id": "e1", "target_id": "e2", "dimension": "trust", "direction": "increase"}),
    ], holders={"trust_holder_id": "e1"})


def _communication(c):
    f, h = "dialogue_communication", "speaker_id"
    _cue(c, f, h, "say", "says", "communication", [
        (h, "entity_ref", "Entity producing the current attributed utterance, not necessarily the narrator.", "e1", ref("person.entity_id")),
        ("speech_act_kind", "string", "Proposed communicative act category; generic utterance remains unresolved until content is available.", "utterance", "utterance"),
        ("utterance_id", "string", "Stable ID of the communication act being discussed; this seed reuses the already identified communication event ID.", "ev2", ref("cue.event_id")),
        ("communication_scope_bundle", "object", "Correlated speaker, communication-event and assertion-scope binding.",
         {"speaker_id": "e1", "utterance_event_id": "ev2", "scope_id": "s1"},
         {"speaker_id": ref("person.entity_id"), "utterance_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("addressee_ids", "array", "Explicit or resolved recipients of an utterance, excluding merely mentioned people.", ["e2"]),
        ("communication_channel", "string", "Explicitly supported communication channel, with no assumption that it was successfully received.", "speech"),
        ("utterance_content_id", "string", "Proposition/question/action ID expressed by the utterance.", "p_request_thread"),
        ("quote_mode", "string", "Whether the content is direct quotation, indirect report, or another represented speech form.", "indirect_report"),
    ])
    _group(c, f, h, "question_answer", "Mia asks Ben where the thread is. He answers that it is in the drawer, and she accepts the answer.",
           "Mia writes the question where is the thread as a handwriting exercise; no one answers it.",
           "A genuine question, bound answer turn and explicit uptake identify the queried slot and response relation.",
           "A displayed question string is not necessarily an act requesting information.", [
        ("question_requested_slot", "string", "Semantic slot whose value the current information-seeking question requests.", "thread_location"),
        ("question_answer_status", "string", "Whether the addressed question remains open or has an explicitly linked response and uptake.", "answered_and_accepted"),
        ("dialogue_response_to_id", "string", "Utterance ID to which the current turn explicitly responds.", "u_thread_in_drawer_answer"),
        ("dialogue_turn_function", "string", "Role of a turn within the exchange, separate from its sentence mood.", "answer_uptake"),
    ])
    _group(c, f, h, "request_and_promise", "Mia asks Ben to bring thread. Ben promises to do it, and Mia says his promise is for her.",
           "Mia wishes Ben would bring thread, but neither asks him nor receives a promise.",
           "An explicit request and responding promise bind requested action, acceptance and beneficiary.",
           "A private wish does not establish a request, accepted task or promise.", [
        ("request_action_id", "string", "Action ID requested from an addressee by a communication act.", "a_bring_thread"),
        ("request_acceptance_status", "string", "Addressee's explicit uptake of a request, distinct from later execution.", "accepted_by_promise"),
        ("promise_content_id", "string", "Proposition/action the promiser explicitly commits to, within the promise's scope.", "p_ben_brings_thread", {"speaker_id": "e2", "addressee_ids": ["e1"]}),
        ("promise_beneficiary_id", "entity_ref", "Entity explicitly identified as beneficiary or promisee for a promise.", "e1", {"speaker_id": "e2", "addressee_ids": ["e1"]}),
    ], holders={"speaker_id": "e1", "addressee_ids": ["e2"]})
    _group(c, f, h, "warning_offer_apology", "Mia warns Ben about the slippery step, offers him her hand, and apologizes for leaving it wet; he accepts her apology.",
           "Mia lists the words warning, offer and apology while Ben listens.",
           "Distinct explicit communicative acts bind a hazard, offered action and past event targeted by apology.",
           "Naming act labels alone does not perform those acts.", [
        ("warning_hazard_id", "string", "Proposition/event ID presented as a hazard in a warning act.", "p_step_slippery"),
        ("offer_content_id", "string", "Action/resource ID explicitly offered to the addressee.", "a_help_with_hand"),
        ("apology_target_event_id", "string", "Past event or conduct explicitly targeted by the apology.", "ev_leave_step_wet"),
        ("apology_acceptance_status", "string", "Addressee's explicit uptake of an apology, separate from forgiveness inferred by silence.", "accepted"),
    ])
    _group(c, f, h, "communication_effect", "Mia explains where the needle is so Ben can find it. Ben repeats the location correctly, and both agree they now know it.",
           "Mia explains the location while Ben is absent and gives no sign of receiving the message.",
           "Stated communicative purpose and observable acknowledged uptake support a bounded success claim.",
           "Producing an utterance does not prove reception or shared understanding.", [
        ("communication_intended_effect", "string", "Speaker's explicit intended change in the addressee's information or behavior.", "ben_can_find_needle"),
        ("communication_success_status", "string", "Evidence-based status of accomplishing the stated communicative purpose.", "acknowledged_understanding"),
        ("utterance_common_ground_delta", "object", "Proposition explicitly accepted as shared in the exchange; not a claim of infinite mutual knowledge.", {"add": ["p_needle_location"], "participants": ["e1", "e2"]}),
        ("communication_illocution_scope", "object", "Scope and force under which content is communicated, preserving who asserts it to whom.", {"force": "explanation", "speaker_id": "e1", "audience_ids": ["e2"]}),
    ], requires=("dialogue_uptake_graph", "scope_resolution", "cross_clause_coreference"))
    _group(c, f, h, "disclosure_and_irony", "Mia admits to Ben that she hid the broken cup to keep him from knowing it was broken. She says her earlier lovely work was sarcasm, not praise, and insists this admission is sincere.",
           "Mia calls the cup lovely, with no evidence of concealment, sarcasm or insincerity.",
           "Explicit retrospective interpretation links disclosure, prior concealment and a speaker-labeled ironic utterance.",
           "Positive wording alone cannot establish sarcasm or a hidden fact.", [
        ("disclosure_content_id", "string", "Content explicitly revealed in a disclosure act.", "p_mia_hid_broken_cup"),
        ("concealment_content_id", "string", "Content explicitly described as withheld from an audience.", "p_cup_broken"),
        ("irony_interpretation", "object", "Attributed nonliteral communicative reading and its evidence, not sentiment inversion by default.", {"utterance": "u_lovely_work", "kind": "speaker_declared_sarcasm"}),
        ("utterance_sincerity_claim", "string", "Scoped claim about a speaker's sincerity, separate from independently verified truth.", "speaker_claims_sincere"),
    ])
    _group(c, f, h, "dialogue_repair", "Mia says the thread is blue, then corrects herself: she meant green. She adds that she saw it and confirms Ben has brought it as promised.",
           "Mia says blue and Ben says green about different threads; neither corrects the other.",
           "Explicit self-correction identifies a target utterance and replacement, with separate evidence and fulfillment claims.",
           "Different words about different referents are not a repair relation.", [
        ("dialogue_repair_target_id", "string", "Utterance or sub-utterance ID explicitly targeted by a correction or clarification.", "u_thread_blue"),
        ("dialogue_repair_kind", "string", "Kind of communicative repair, such as correction, clarification or disambiguation.", "self_correction"),
        ("utterance_evidence_type", "string", "Evidence type the speaker explicitly invokes for the communicated claim.", "visual_observation"),
        ("promise_fulfillment_claim", "object", "Scoped communicative claim that an earlier promise was fulfilled, preserving its source.", {"promise_id": "u_bring_thread_promise", "claimed_by": "e1", "status": "fulfilled"}),
    ], requires=("dialogue_repair_graph", "scope_resolution", "cross_clause_coreference"))


def _discourse(c):
    f, h = "discourse_cohesion", "discourse_anchor_entity_id"
    _cue(c, f, h, "contrast", "contrasts", "discourse_comparison", [
        (h, "entity_ref", "Entity explicitly organizing or presenting the current discourse comparison, where one is attributed.", "e1", ref("person.entity_id")),
        ("discourse_relation_kind", "string", "Proposed rhetorical relation between discourse units, separate from physical causal relations.", "contrast", "contrast"),
        ("discourse_segment_status", "string", "Incremental status of the current discourse unit or relation before all arguments are available.", "relation_open", "relation_open"),
        ("discourse_scope_bundle", "object", "Correlated presenter, discourse-act event and scope for a rhetorical interpretation.",
         {"presenter_id": "e1", "discourse_event_id": "ev2", "scope_id": "s1"},
         {"presenter_id": ref("person.entity_id"), "discourse_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("discourse_unit_id", "string", "Stable identifier of the discourse unit currently referenced or summarized.", "d_repair_explanation"),
        ("discourse_topic_id", "string", "Entity/proposition/question ID serving as the explicitly supported discourse topic.", "p_kite_repair"),
        ("discourse_focus_id", "string", "Information unit presented as the current focus or answer contribution.", "p_thread_location"),
        ("discourse_background_ids", "array", "Previously established information units treated as background for the current contribution.", ["p_kite_torn"]),
    ])
    _group(c, f, h, "explicit_contrast", "Mia contrasts the two repairs: Ben's patch is quick, whereas hers is strong.",
           "Mia mentions two repairs without comparing any property.",
           "An explicit comparison binds two discourse units, a contrast dimension and their alternatives.",
           "Mentioning two objects is not enough to identify a rhetorical contrast.", [
        ("discourse_relation_source_id", "string", "First or supporting discourse unit bound by the rhetorical relation.", "d_ben_patch_quick"),
        ("discourse_relation_target_id", "string", "Second or targeted discourse unit bound by the rhetorical relation.", "d_mia_patch_strong"),
        ("discourse_contrast_dimension", "string", "Property or evaluative axis explicitly contrasted between discourse units.", "repair_advantage"),
        ("discourse_alternative_set", "array", "Alternatives made salient by the discourse operation, without assuming mutual exclusivity.", ["p_patch_quick", "p_patch_strong"]),
    ])
    _group(c, f, h, "information_packaging", "About the torn kite, Mia says the new fact is that Ben found thread; the tear was already known and the thread is now the main point.",
           "Mia repeats several unrelated sentences without marking what is new, given or central.",
           "The prefix explicitly marks a topic, a new contribution, shared background and relative focus.",
           "Recency alone does not establish information status or discourse importance.", [
        ("discourse_new_information", "array", "Proposition IDs explicitly introduced as new relative to the current common ground.", ["p_ben_found_thread"]),
        ("discourse_given_information", "array", "Proposition IDs explicitly treated as already established in the discourse.", ["p_kite_torn"]),
        ("discourse_salience_rank", "number", "Relative rank of a discourse item under an explicit local ordering; 1 denotes the primary item.", 1),
        ("discourse_grounding_status", "string", "Whether a contribution is proposed, acknowledged or explicitly treated as shared.", "background_acknowledged"),
    ])
    _group(c, f, h, "elaboration_examples_summary", "Mia explains the repair in more detail, gives sewing the tear as an example, and summarizes it as making the kite fly again.",
           "Mia mentions sewing and flying in different stories without linking them as explanation or summary.",
           "Explicit discourse operators connect detail, example and summary to an earlier repair unit.",
           "Shared vocabulary across unrelated units does not create these discourse relations.", [
        ("discourse_elaboration_target", "string", "Discourse unit expanded by the current detailed contribution.", "d_repair"),
        ("discourse_example_target", "string", "General claim or category illustrated by the current example.", "d_repair_methods"),
        ("discourse_summary_target", "string", "Discourse span/unit whose content the current contribution summarizes.", "d_repair_steps"),
        ("discourse_explanation_target", "string", "Claim or event description that the current discourse contribution explains.", "d_kite_can_fly"),
    ])
    _group(c, f, h, "rhetorical_dependency", "Mia corrects her earlier claim that the repair failed: although it looks rough, it flies; if the wind holds, they can test it, so she calls it useful.",
           "Mia lists failed, rough, wind and useful as vocabulary words.",
           "Explicit correction, concession, condition and conclusion cues bind distinct rhetorical targets.",
           "Cue words in a lexical list do not instantiate discourse dependencies.", [
        ("discourse_correction_target", "string", "Earlier discourse claim explicitly revised by the current contribution.", "d_repair_failed"),
        ("discourse_concession_target", "string", "Discourse claim retained while its expected implication is explicitly resisted.", "d_repair_looks_rough"),
        ("discourse_condition_target", "string", "Discourse proposition whose relevance or assertion is conditional on another unit.", "d_can_test_kite"),
        ("discourse_result_target", "string", "Prior discourse material from which the speaker presents a conclusion; not necessarily physical cause.", "d_kite_flies"),
    ], requires=("discourse_relation_graph", "scope_resolution", "operator_scope_binding"))
    _group(c, f, h, "topic_navigation", "Mia first asks how to repair the kite, then turns to lunch, and finally says she is returning to the repair question by asking where the thread is; Ben has not answered yet.",
           "Mia repeats kite and lunch in a shopping list without discourse transitions or a question-answer pair.",
           "Explicit ordering and topic transitions maintain an unanswered question stack.",
           "Repeated nouns do not establish a topic return or answer relation.", [
        ("discourse_sequence_target", "string", "Prior discourse unit ordered before the current contribution in presentation order.", "d_lunch"),
        ("discourse_topic_shift", "object", "Explicit transition from one discourse topic to another.", {"from": "p_kite", "to": "p_lunch"}),
        ("discourse_topic_return", "string", "Previously active topic explicitly resumed after an intervening segment.", "p_kite"),
        ("discourse_question_stack", "array", "Ordered currently open questions tracked by the discourse, with the last item active.", ["q_kite_repair", "q_thread_location"]),
    ], requires=("discourse_stack", "scope_resolution", "question_answer_binding"))
    _group(c, f, h, "implicit_bridge_and_accommodation", "Mia asks where the thread is. Ben says the sewing box is open; she takes that as an indirect answer but says she must assume the thread is inside.",
           "Mia asks where the thread is. Ben says he likes apples, and she says this does not answer her question.",
           "The listener explicitly interprets an indirect answer and states its bridging assumption, preserving uncertainty.",
           "An unrelated response cannot be silently repaired into an answer without supporting evidence.", [
        ("discourse_answer_relation", "object", "Relation between a question and a direct or explicitly interpreted indirect answer.", {"question": "q_thread_location", "answer": "d_box_open", "kind": "indirect_attributed"}),
        ("discourse_implicit_relation", "object", "Rhetorical relation inferred by a participant rather than marked directly.", {"kind": "answer", "interpreter_id": "e1", "status": "tentative"}),
        ("discourse_bridge_assumption", "string", "Proposition explicitly needed to connect two discourse units but not established by them.", "p_thread_in_box"),
        ("discourse_accommodation", "object", "Provisional addition to discourse assumptions, with source and non-factual status retained.", {"content": "p_thread_in_box", "status": "assumed_for_interpretation"}),
    ], requires=("discourse_relation_graph", "scope_resolution", "assumption_tracking"))


def _reasoning(c):
    f, h = "reasoning_memory", "reasoner_id"
    _cue(c, f, h, "infer", "infers", "reasoning", [
        (h, "entity_ref", "Entity to whom an inference or reasoning process is attributed.", "e1", ref("person.entity_id")),
        ("reasoning_mode", "string", "Kind of represented cognitive process, not an assertion of its validity.", "inference", "inference"),
        ("reasoning_validity_claim", "string", "Evidence status of an inference's validity; an inference verb alone leaves validity unassessed.", "unassessed", "unassessed"),
        ("reasoning_scope_bundle", "object", "Correlated reasoner, reasoning-event and discourse-scope binding.",
         {"reasoner_id": "e1", "reasoning_event_id": "ev2", "scope_id": "s1"},
         {"reasoner_id": ref("person.entity_id"), "reasoning_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("reasoning_content_id", "string", "Problem or proposition ID that the represented reasoning addresses.", "q_where_thread"),
        ("reasoning_conclusion_id", "string", "Proposition ID presented as the result of the reasoner's inference.", "p_thread_in_box"),
        ("reasoning_premise_ids", "array", "Propositions explicitly used as premises by the reasoner, preserving their assertion scopes.", ["p_thread_stored_after_use", "p_box_last_used"]),
        ("reasoning_rule_kind", "string", "Explicitly represented inferential relation, such as analogy, elimination or causal explanation.", "elimination"),
    ])
    _group(c, f, h, "reasoning_challenge", "Mia claims every tool is always in the box and thread is a tool, so the thread must be there; then she admits she has seen thread stored elsewhere and has not checked today.",
           "Mia sees the thread in the open box and makes no generalization or admission of missing evidence.",
           "The reasoner states a conclusion, a defeater and a missing check, allowing bounded critique of her inference.",
           "Direct observation is not the same witness as an explicitly challenged generalization.", [
        ("reasoning_evidence_gap", "string", "Missing premise or observation explicitly acknowledged or formally required by the represented inference.", "p_current_box_contents_unchecked"),
        ("reasoning_counterexample_ids", "array", "Propositions/events explicitly offered as counterexamples to a generalization.", ["p_thread_sometimes_stored_elsewhere"]),
        ("reasoning_contradiction", "object", "Incompatible proposition pair within one holder's reasoning scope, with the conflict type specified.", {"generalization": "p_all_tools_always_in_box", "counterexample": "p_thread_previously_elsewhere", "kind": "universal_counterexample"}),
        ("reasoning_explanation_id", "string", "Proposition graph or explanation ID offered to support the conclusion.", "x_tool_storage_argument"),
    ], requires=("reasoning_graph", "scope_resolution", "typed_contradiction_check"))
    _group(c, f, h, "hypothesis_selection", "Mia considers the drawer and the box. She chooses the drawer because Ben just saw the thread there, then drops her earlier box guess.",
           "Mia says drawer and box while reading a furniture list, without choosing a location.",
           "Explicit alternatives, an evidence-based choice and a revision describe a holder's hypothesis selection.",
           "Listing candidate words does not establish considered hypotheses or a selection criterion.", [
        ("reasoning_alternative_hypotheses", "array", "Proposition IDs explicitly considered as competing explanations or answers.", ["p_thread_in_drawer", "p_thread_in_box"]),
        ("reasoning_selection_criterion", "string", "Stated basis for preferring one considered hypothesis over another.", "recent_witness_report"),
        ("reasoning_revision", "object", "Change in the reasoner's selected conclusion with its stated basis.", {"old": "p_thread_in_box", "new": "p_thread_in_drawer", "basis": "p_ben_saw_thread"}),
        ("mental_comparison_basis", "string", "Dimension on which the reasoner explicitly compares alternatives.", "quality_of_location_evidence"),
    ], requires=("reasoning_graph", "scope_resolution", "hypothesis_revision_tracking"))
    _group(c, f, h, "analogy_and_counterfactual", "Mia compares mending the kite to patching a sail: the cloth and tears play corresponding roles. She imagines using strong thread instead of the weak thread she has, so the tear would not reopen.",
           "Mia names a kite and a sail but makes no comparison or imagined change.",
           "An explicit analogy maps roles, while a counterfactual alters one premise and derives an imagined outcome.",
           "Shared materials alone do not establish the reasoner's analogy or counterfactual inference.", [
        ("reasoning_analogy_source_id", "string", "Source-domain event/frame explicitly used to reason about a different target.", "frame_patch_sail"),
        ("reasoning_analogy_mapping", "object", "Explicit role/property correspondences in an analogy, not identity between the domains.", {"sail_cloth": "kite_cloth", "sail_tear": "kite_tear"}),
        ("mental_counterfactual_change", "object", "Altered premise in an explicitly imagined alternative to a known situation.", {"replace": "p_thread_weak", "with": "p_thread_strong"}),
        ("mental_simulation_outcome", "string", "Outcome proposition generated or stated within a mental simulation, not committed narrator fact.", "p_tear_does_not_reopen"),
    ], requires=("analogy_role_mapping", "counterfactual_scope", "proposition_binding"))
    _group(c, f, h, "remembered_event", "Mia remembers lending Ben the needle yesterday; she says the memory is vivid but the color is unclear.",
           "Mia imagines lending Ben a needle tomorrow and says it has never happened.",
           "An explicit memory attitude anchors content to a past event and reports different quality dimensions.",
           "A hypothetical future scene is not a remembered past event.", [
        ("mental_memory_holder_id", "entity_ref", "Entity reporting or attributed the episodic memory, distinct from a runtime cache owner.", "e1"),
        ("mental_memory_content_id", "string", "Proposition ID represented as remembered content.", "p_mia_lent_needle"),
        ("mental_memory_event_id", "string", "Past event ID to which an episodic memory claim refers.", "ev_lend_needle"),
        ("mental_memory_vividness", "string", "Holder's explicit report of experiential vividness, not accuracy.", "vivid"),
    ], holders={"reasoner_id": "e1", "mental_memory_holder_id": "e1"})
    _group(c, f, h, "memory_source_check", "The drawer reminds Mia of lending the needle. She cannot recall every detail and wonders whether she saw it herself or only heard Ben tell the story; the record later confirms the loan.",
           "Mia reads a loan record for the first time and does not claim any memory of the event.",
           "The prefix explicitly supplies a retrieval cue, incomplete recall, uncertain source and external corroboration.",
           "Reading a record without a memory claim does not establish a remembered experience or source confusion.", [
        ("mental_memory_retrieval_cue", "string", "Entity, perception or proposition explicitly described as eliciting recall.", "p_seeing_drawer"),
        ("mental_memory_completeness", "string", "Holder's report of how much relevant episodic detail is recalled.", "partial"),
        ("mental_memory_source_confusion", "object", "Explicit uncertainty about whether remembered content came from experience, testimony, imagination or another source.", {"alternatives": ["own_perception", "ben_testimony"]}),
        ("mental_memory_accuracy_claim", "string", "Scoped comparison of a memory claim with available corroborating or conflicting evidence.", "event_corroborated_details_unresolved"),
    ], requires=("memory_claim_graph", "scope_resolution", "source_comparison"), holders={"reasoner_id": "e1", "mental_memory_holder_id": "e1"})
    _group(c, f, h, "purposeful_imagination", "Mia imagines a kite flying in a world with no wind, just to test what her plan assumes; she says this is pretend.",
           "Mia watches a real kite fly and gives no indication that the scene is imagined.",
           "An explicit imagination operator introduces a separate world and a stated cognitive purpose.",
           "An ordinary perception cannot be moved into an imagined world without evidence.", [
        ("imaginer_id", "entity_ref", "Entity constructing or experiencing an explicitly imagined scene.", "e1"),
        ("imagined_content_id", "string", "Proposition ID asserted inside an imagination scope rather than the narrator world.", "p_kite_flies_without_wind"),
        ("imagined_world_id", "string", "Identifier for the alternate situation containing imagined content.", "w_no_wind"),
        ("imagination_function", "string", "Explicit purpose attributed to the imaginative act, without assuming all imagining is planning.", "test_plan_assumption"),
    ], requires=("mental_world_scope", "proposition_binding", "purpose_binding"))


def _narrative(c):
    f, h = "narrative_perspective", "focalizer_id"
    _cue(c, f, h, "notice", "notices", "perception", [
        (h, "entity_ref", "Entity whose current perception anchors a candidate viewpoint; does not by itself establish global focalization.", "e1", ref("person.entity_id")),
        ("viewpoint_access", "string", "Mode of access supported for the local viewpoint, distinct from omniscient narrator access.", "perceptual_local", "perceptual_local"),
        ("viewpoint_perceptual_anchor", "string", "Perception event anchoring the current local viewpoint candidate.", "ev2", ref("cue.event_id")),
        ("narrative_scope_bundle", "object", "Correlated local focalizer, access event and assertion scope.",
         {"focalizer_id": "e1", "access_event_id": "ev2", "scope_id": "s1"},
         {"focalizer_id": ref("person.entity_id"), "access_event_id": ref("cue.event_id"), "scope_id": ref("cue.scope_id")}),
    ])
    _carry(c, f, h, [
        ("narrator_id", "entity_ref", "Represented narrator identity when explicitly grounded; an unpersonified narrator remains unknown.", "e3"),
        ("narration_person", "string", "Grammatical person used for the explicitly bound narrator's telling, not focalizer identity.", "first_person"),
        ("viewpoint_entity_scope", "array", "Entities whose perceptions or internal states the local passage explicitly accesses.", ["e1"]),
        ("viewpoint_evaluative_stance", "object", "Evaluation attributed to the viewpoint holder rather than adopted as narrator fact.", {"holder_id": "e1", "target": "p_repair", "stance": "hopeful"}),
    ])
    _group(c, f, h, "narrator_position", "Mia tells the story herself: I was there, though I may remember it wrongly; I now see my younger self with some distance.",
           "An unnamed narrator describes Mia from outside without identifying a teller or evaluating memory.",
           "An explicitly identified participant narrator states involvement, uncertainty and retrospective distance.",
           "A third-person character mention does not establish narrator identity, reliability or distance.", [
        ("narrator_reliability_claim", "string", "Textual claim about a narrator's reliability, preserving whether it is self-attributed or externally attributed.", "self_acknowledged_uncertainty"),
        ("narrator_involvement", "string", "Narrator's explicitly established participation in the narrated events.", "participant"),
        ("narrator_distance", "string", "Explicit temporal or evaluative distance between telling self and experiencing self.", "retrospective_reflective"),
        ("viewpoint_knowledge_boundary", "object", "Explicit limit on what the viewpoint/narrator can know at the represented moment.", {"holder_id": "e1", "limit": "memory_may_be_inaccurate"}),
    ])
    _group(c, f, h, "viewpoint_and_time_framing", "Mia stops describing what she saw and tells what Ben noticed. Then she goes back to the morning and expands the scene, describing each movement in detail.",
           "Mia mentions Ben and morning while continuing the same present scene without changing perspective.",
           "Explicit narration cues shift perceptual holder, temporal frame, presentation order and telling pace.",
           "Mentioning another person or time does not by itself shift viewpoint or narrative frame.", [
        ("viewpoint_shift", "object", "Explicit transition between viewpoint anchors in the discourse.", {"from": "e1", "to": "e2"}),
        ("narrative_time_frame", "string", "Time frame selected by the telling, distinct from raw event chronology.", "earlier_morning"),
        ("narrative_order_mode", "string", "Relation of the current telling segment to already presented story time.", "retrospective_return"),
        ("narrative_pace", "string", "Explicitly supported telling pace or granularity, not an invented numeric rate.", "expanded_scene"),
    ], requires=("narrative_frame_tracking", "scope_resolution", "viewpoint_transition_binding"))
    _group(c, f, h, "scene_thread_opening", "Mia begins a new scene in the workshop. Again she tells of repairing kites, but this time the missing needle leaves the repair unfinished.",
           "Mia lists workshop, kite and needle without narrating events or opening a problem.",
           "An explicit scene boundary and recurring event presentation introduce a particular unresolved repair thread.",
           "A lexical list has no scene transition, narrative recurrence or unresolved event thread.", [
        ("narrative_scene_id", "string", "Identifier for a bounded scene segment supported by place/time or explicit transition evidence.", "scene_workshop"),
        ("narrative_frequency_mode", "string", "Whether the telling presents a single instance, recurring pattern or repeated telling of an event.", "recurring_activity_specific_instance"),
        ("narrative_thread_id", "string", "Stable identifier for an explicitly sustained issue or action line.", "thread_kite_repair"),
        ("narrative_thread_status", "string", "Prefix-supported lifecycle state of the narrative issue; lack of future text does not prove closure.", "open"),
    ])
    _group(c, f, h, "problem_and_goal_link", "Mia says the lost needle is the problem preventing her kite repair. She wants it found, and only finding it will settle this part of the story.",
           "Mia mentions a lost needle as a joke unrelated to the kite she is repairing.",
           "Explicit discourse links a problem, a goal and its stated resolution criterion within one thread.",
           "A thematically similar but unrelated mention cannot inherit the current thread's goal.", [
        ("narrative_problem_id", "string", "Proposition/question ID explicitly functioning as a problem in the current narrative thread.", "p_needle_missing"),
        ("narrative_goal_link", "object", "Link between a narrative thread and an explicitly relevant character goal.", {"thread": "thread_kite_repair", "goal": "g_find_needle"}),
        ("narrative_expectation", "object", "Prefix-supported expectation about a possible continuation, kept distinct from a future fact.", {"content": "p_needle_found", "status": "desired_resolution"}),
        ("narrative_tension_source", "string", "Explicitly supported unresolved opposition or uncertainty sustaining the current thread.", "goal_blocked_by_missing_tool"),
    ])
    _group(c, f, h, "visible_change_and_resolution", "Mia finds the needle and finishes the kite. She says the search is over; the kite now flies where it could not before.",
           "Mia imagines finding the needle, but the real search and torn kite remain unchanged.",
           "Visible real-scope outcomes satisfy a prior thread criterion and demonstrate a before/after change.",
           "Imagined success cannot close the actual search thread or prove physical change.", [
        ("narrative_resolution_evidence", "object", "Prefix-visible outcome tied to the stated criterion of an earlier problem.", {"problem": "p_needle_missing", "outcome": "p_needle_found", "status": "explicitly_closed"}),
        ("narrative_change_dimension", "string", "Dimension along which the narrated before/after state is explicitly contrasted.", "kite_flight_capability"),
        ("narrative_change_evidence", "object", "Bound earlier and later propositions supporting a change interpretation.", {"before": "p_kite_cannot_fly", "after": "p_kite_flies"}),
        ("narrative_tension_status", "string", "Status of a specified tension under the visible evidence, not global story quality.", "resolved_for_search_thread"),
    ], requires=("narrative_thread_graph", "scope_resolution", "resolution_criterion_comparison"))
    _group(c, f, h, "interpretive_pattern_and_closure", "Mia says she expected failure, so the flying kite surprises her. She recalls the earlier image of torn cloth and points to the cloth now mended, calling its return a reminder that patient work helps; she says this is where her tale ends.",
           "The prefix only says Mia sees cloth; no prior expectation, repeated image, lesson or ending cue has appeared.",
           "The prefix explicitly provides surprise, a repeated-image interpretation, a stated theme and an ending cue.",
           "An isolated image cannot prove foreshadowing, a theme, surprise or eventual closure.", [
        ("narrative_surprise_evidence", "object", "Contrasted expectation and outcome attributed to a perceiver or teller.", {"holder_id": "e1", "expected": "p_repair_fails", "observed": "p_kite_flies"}),
        ("narrative_theme_candidate", "object", "Explicitly stated or evidence-supported thematic interpretation, labeled as a candidate rather than ground truth.", {"content": "patient_work_can_help", "source_id": "e1", "status": "stated_interpretation"}),
        ("narrative_motif_link", "object", "Relation among recurring images/events with a supported interpretive link.", {"earlier": "d_torn_cloth", "current": "d_mended_cloth", "relation": "transformed_return"}),
        ("narrative_closure_candidate", "object", "Evidence that the current prefix can serve as a closing unit, without seeing future text.", {"cue": "explicit_tale_end", "thread": "thread_kite_repair", "status": "candidate"}),
    ], requires=("narrative_thread_graph", "scope_resolution", "interpretation_provenance"))


def _belief_suppression(c):
    """Use four epistemic classifications to specify actual inhibitory heads.

    The classification remains an associated catalog concept. This head lowers
    the exact old value's residual support; it does not produce its metadata.
    """
    designs = [
        ("belief_revision", "belief_content_id", "p_open_gate", "explicit_belief_replacement",
         "Mia believed the gate was open. She checks it, explicitly changes her mind, and now believes it is shut.",
         "Mia believes the gate is open. Ben checks it and finds it shut but does not tell Mia, who still believes it is open.",
         "The same holder explicitly replaces the earlier bound belief with a different content after receiving evidence.",
         "Other characters' observations, narrator truth, or a merely competing belief do not establish replacement by this holder.",
         "attitude_revision_graph"),
        ("belief_error_status", "belief_polarity", "accepts", "acknowledged_belief_error",
         "Mia accepted the claim that the gate was open. After learning it was shut all along, she acknowledges her error and explicitly withdraws that acceptance.",
         "Mia accepts the claim that the gate is open. The narrator shows it is shut, but Mia has not learned this and still accepts the claim.",
         "The holder receives evidence of the same-time error, acknowledges it and explicitly withdraws acceptance of the bound proposition.",
         "A false belief may remain genuinely held. Contradiction known only to the narrator must not suppress its attribution to the uninformed holder.",
         "holder_acknowledged_retraction"),
        ("epistemic_resolution_status", "epistemic_alternatives", ["p_open_gate", "p_shut_gate"], "settled_epistemic_alternative_set",
         "Mia considers both possibilities: the gate is open or it is shut. She checks it and says she now knows it is shut and the question is settled.",
         "Mia considers both possibilities: the gate is open or it is shut. Ben checks it, but Mia does not learn what he found and remains unsure.",
         "The holder explicitly settles the same previously represented question; withdraw the old unresolved alternative-set value.",
         "Another holder settling the question cannot remove this holder's uncertainty. Do not interpret suppression of the set as falsity of all members.",
         "holder_question_resolution"),
        ("epistemic_time_scope", "belief_content_id", "p_open_gate", "explicit_belief_validity_end",
         "Mia says she believed the gate was open until noon, when she stopped holding that belief. It is now after noon and she explicitly says she no longer holds it.",
         "Mia said at noon that she believed the gate was open. It is now later, but nothing says she changed or stopped holding that belief.",
         "An explicit end of this holder's attitude attribution precedes the query, and the holder confirms that the old belief is no longer held.",
         "Elapsed time or missing fresh evidence alone cannot expire a belief attribution; require the explicit termination boundary.",
         "attitude_interval_applicability"),
    ]
    by_key = {a["key"]: (a, h, g) for a, h, g in zip(c.attributes, c.heads, c.grammars)}
    for concept, target, value, mechanism, good, bad, condition, contrast, capability in designs:
        attribute, head, grammar = by_key[concept]
        target_attribute = by_key[target][0]
        positive, negative = _context(good), _context(bad)
        # The first clause already licenses the old evidence at its final word.
        for context in (positive, negative):
            source = next((row for row in context if row["token"] == "open"), context[0])
            source.update({target: value, "belief_holder_id": "e1", "event_id": "ev_prior_belief"})
        name = f"suppress_{target}_on_{mechanism}"
        function = f"{condition} Lower support for the exact earlier {target} value at the current query; assert no opposite value."
        reads = sorted({target, "belief_holder_id", "event_id", "scope_id", "assertion_status", "token"})
        requires = [capability, "claim_identity_alignment", "scope_resolution"]
        head.update(name=name, function=function, mechanism=mechanism, operation="suppress",
                    reads=reads, writes=[target], requires=requires,
                    attribute_ids=[attribute["id"], target_attribute["id"]])
        head["evaluation"]["intervention"] = (
            "Keep narrator evidence fixed but hide the correction from the holder; suppression must stop. "
            "When the holder explicitly updates, only the aligned old value loses evidence; no false value is introduced.")
        grammar.update(name=name, intent=function, reads=reads, writes=[target], requires=requires,
                       attribute_ids=[attribute["id"], target_attribute["id"]],
                       examples=[dict(example(positive, {target: value}, condition), polarity="positive"),
                                 dict(example(negative, {}, contrast), polarity="contrastive")])
        grammar["contract"] = {
            "match": {
                "domain": "visible_prefix",
                "binders": {"prior": "earlier attributed belief/question record with exact value and content anchor",
                            "holder": "prior.belief_holder_id", "update": condition,
                            "query": "current final prefix token"},
                "selection": "Align the same holder, proposition/question, semantic world and applicable time; retain other claims.",
            },
            "guards": [contrast, "All sources precede or equal the query.",
                       "The update is actual in the holder's attitude scope, not merely dreamed, quoted as an unaccepted claim, or available only to someone else.",
                       "Target a known earlier value. Missing old evidence yields NOOP rather than a synthesized negation."],
            "emit": {target: {"copy": f"prior.{target}"}},
            "operation": "suppress",
            "effect": "Subtract evidence from the aligned old field/value at the current query. Do not edit earlier latents or assert the opposite value.",
        }
        attribute["producer_head_ids"] = []
        attribute["associated_head_ids"] = [head["id"]]
        attribute["notes"] = (attribute.get("notes", "") + " The linked inhibitory head uses this classification as its applicability concept; it suppresses another field and does not itself emit this metadata.").strip()
        grammar["ambiguity_notes"] = "Requires claim-aligned inhibition. The expected patch lists the value whose score is lowered, not a new positive assertion."


def _require_correlated_routing(c):
    """Keep executable matchers without claiming their flat writes are safe.

    The runtime sums field/value scores independently. A mental interpretation
    needs a joint holder/content/event/scope tuple, including its own status.
    These adapter records preserve exact finite matcher seeds for later reuse.
    """
    for attribute, head, grammar in zip(c.attributes, c.heads, c.grammars):
        if grammar["runtime_support"] != "native":
            continue
        seed = grammar.pop("neuron")
        carry = head["mechanism"] == "entity_keyed_scoped_evidence_copy"
        requirements = ["correlated_hypothesis_routing", "scoped_candidate_storage"]
        if not carry:
            requirements.append("construction_role_binding")
        explanation = (
            "The finite seed matcher is executable, but this complete head requires an adapter: "
            "commit holder, value, event, scope and candidate status as one correlated alternative. "
            "Current fieldwise merging can construct a tuple absent from every source and can leave "
            "an observed asserted status winning over a new candidate status. Do not apply the seed's "
            "flat emission directly to the residual. Example expectations describe one logical candidate, "
            "not the current runtime's flattened residual view.")
        grammar["contract"] = {
            "seed_matcher": seed,
            "seed_role": "Exact executable finite matcher/projection for producing candidate contents before atomic routing; not a complete native head.",
            "match": {
                "domain": "visible_prefix",
                "finite_pattern": "seed_matcher.rules[*].pattern",
                "binders": (["prior", "mention"] if carry else ["person", "cue"]),
                "query": "last visible token",
                "selection": ("Match the query entity and scope to an earlier holder-specific source; keep every source derivation distinct."
                              if carry else "Match the adjacent annotated entity/verb construction in one scope; keep every construction derivation distinct."),
            },
            "guards": [
                "Every source is at or before the query; holder identity and scope must match the finite seed constraints.",
                "Never select fieldwise winners from different derivations to assemble a new tuple.",
                "Candidate status belongs to the new interpretation envelope, independently of the input token's assertion status.",
                ("Earlier asserted evidence licenses a retrieved candidate only; it does not establish continued truth, freshness, or the holder's present attitude."
                 if carry else "Bind the cue's subject/experiencer/attitude-holder role to person.entity_id; adjacency alone is insufficient, as in 'the friend of Mia believes'. An annotated verb sense licenses only a provisional construction and does not resolve an unseen complement."),
            ],
            "emit": seed["rules"][0]["emit"],
            "hypothesis_envelope": {
                "fields": "the complete resolved emit mapping from one derivation",
                "assertion_status": "candidate",
                "support": "source token positions and capture identities from that same derivation",
                "joint_selection": "select or retain this complete envelope atomically; never independently merge its member fields",
            },
            "effect": "Add a correlated interpretation candidate at the current query through the adapter; preserve observed token metadata and historical records.",
            "ambiguity": "Retain distinct source/holder/event/scope tuples as alternatives, or choose one complete tuple with NOOP available. No latest-source inference is implied.",
        }
        grammar.update(runtime_support="adapter_required", requires=requirements,
                       ambiguity_notes=grammar["ambiguity_notes"] + " " + explanation)
        head.update(runtime_support="adapter_required", requires=requirements,
                    routing="adapter_selects_or_retains_complete_correlated_candidates_with_noop")
        attribute["notes"] = attribute.get("notes", "") + " " + explanation


def build():
    catalog = Catalog("mind", 769)
    for builder in (_epistemic, _goals, _affect, _social, _communication, _discourse, _reasoning, _narrative):
        before = len(catalog.attributes)
        builder(catalog)
        assert len(catalog.attributes) - before == 32, builder.__name__
    _belief_suppression(catalog)
    _require_correlated_routing(catalog)
    assert len(catalog.attributes) == 256
    return catalog.records()
