"""Curated identity, time, quantity, evidence and semantic-retrieval candidates.

Rows name distinct contracts. Shared authoring functions remove JSON boilerplate;
they do not turn lexical examples into demonstrated semantic algorithms.
"""

from copy import deepcopy

from ..schema import Catalog, example, gap, neuron, one_of, present, ref, seq, tok


LOCAL = ("local.storyformer", "local.attribute_grammar")


def _native(c, key, typ, definition, family, value, pattern, emit, positive, negative,
            *, name=None, mechanism="feature_projection", scope="current mention",
            sources=LOCAL, tables=None, notes="", operation="add"):
    c.add(key, typ, definition, family, value=value, scope=scope,
          head=name or f"Project {key.replace('_', ' ')}", function=definition,
          mechanism=mechanism, native=neuron(pattern, {key: emit}, tables=tables),
          positive=example(positive, {key: value}, "The prefix supplies the tested evidence and all copied values."),
          negative=example(negative, {}, "The decisive evidence or identity constraint is absent; abstain."),
          operation=operation, sources=sources, notes=notes)


def _lookup(c, key, typ, definition, family, values, *, field="token", scope="lexical mention",
            sources=LOCAL, notes="", tests=None):
    # Words such as "second", "since", "about" and "quarter" have unrelated
    # readings. A semantic lookup consumes a selected sense, not spelling alone.
    sense_families = {
        "assertion_status": "source_marker", "referent_kind": "referential",
        "mention_form": "reference_form", "temporal_signal_relation": "temporal_connective",
        "temporal_deixis": "time_deictic", "temporal_granularity": "time_unit",
        "temporal_frequency_class": "temporal_frequency", "temporal_phase_cue": "event_phase",
        "temporal_order_cue": "temporal_order", "temporal_bound_cue": "temporal_bound",
        "calendar_day_name": "weekday", "ordinal_rank": "ordinal",
        "measure_dimension": "measure_unit", "measure_unit": "measure_unit",
        "quantity_comparison_cue": "quantity_comparison", "quantity_approximation_cue": "quantity_modifier",
        "quantity_distribution_cue": "distributive", "quantity_fraction_lexeme": "fraction",
        "evidence_source_kind": "evidence_marker",
    }
    surfaces = {}
    if field == "token" and key in sense_families:
        surfaces = {f"{word}:{sense_families[key]}": word for word in values}
        values = {sense: values[word] for sense, word in surfaces.items()}
        field = "lexical_sense_id"
        notes += " Requires a causally selected lexical sense; an unrelated known sense must abstain."
    aliases = {"scissors:tool": "scissors.n.01", "rabbit:animal": "rabbit.n.01"}
    if field == "lexical_sense_id":
        values = {aliases.get(sense, sense): value for sense, value in values.items()}
    first, val = next(iter(values.items()))
    tests = dict(tests or {})
    if key == "cardinal_value":
        tests["pos"] = "num"
    pattern = seq(gap(), tok("cue", **{field: one_of(*values), **tests}))
    surface = surfaces.get(first, first.split(":")[0].split(".")[0])
    positive = [{"token": surface, field: first, **tests}]
    negative = [{"token": surface, field: "__incompatible_sense__", **tests}] if field != "token" else [{"token": "__unlisted__", **tests}]
    _native(c, key, typ, definition, family, val, pattern,
            {"$lookup": {"table": "mapping", "key": ref(f"cue.{field}")}}, positive, negative,
            mechanism="finite_semantic_lookup", scope=scope, sources=sources,
            tables={"mapping": values}, notes=notes or
            "Finite seed table only; values describe a cue/sense, not a committed world fact. Expand from evidence.")


def _carry(c, key, typ, definition, family, value, *, identity="entity_id", scope="mention",
           sources=LOCAL, claim_aligned=False):
    prior = {"token": "earlier", identity: "e1" if identity.endswith("entity_id") else "ev1",
             "scope_id": "s1", key: value}
    current = {"token": "again", identity: prior[identity], "scope_id": "s1"}
    bad = {**current, identity: "e2" if identity.endswith("entity_id") else "ev2"}
    source_tests = {key: present(), identity: present(), "scope_id": present()}
    query_tests = {identity: ref(f"source.{identity}"), "scope_id": ref("source.scope_id")}
    notes = "Copies only the immediately preceding record with the same identity and scope. This seed does not resolve identity, select the latest distant fact, or prove persistence."
    if claim_aligned:
        # Equal event IDs are insufficient: two sources can disagree about it.
        prior["source_claim_id"] = "p1"
        source_tests["source_claim_id"] = present()
        if key == "source_claim_id":
            # Project a claim ID only after its joint anchor was selected; do
            # not put the requested output into the query and copy it back.
            current["evidence_anchor_bundle"] = {"claim_id": "p1", "event_id": prior[identity], "scope_id": "s1"}
            query_tests["evidence_anchor_bundle.claim_id"] = ref("source.source_claim_id")
            bad = {**current, "evidence_anchor_bundle": {**current["evidence_anchor_bundle"], "claim_id": "p2"}}
        else:
            current["source_claim_id"] = "p1"
            query_tests["source_claim_id"] = ref("source.source_claim_id")
            bad = {**current, "source_claim_id": "p2"}
        notes += " Provenance transfer additionally requires the same already selected source claim; matching event/scope alone cannot join distinct reports. The source_claim_id projection reads the query's correlated evidence anchor instead of resolving a new claim by event similarity."
    _native(c, key, typ, definition, family, value,
            seq(gap(), tok("source", **source_tests), tok(**query_tests)),
            ref(f"source.{key}"), [prior, current], [prior, bad],
            mechanism="same_identity_adjacent_copy", scope=scope, sources=sources,
            notes=notes)


def _contract(c, key, typ, definition, family, value, *, condition, transform,
              positive, negative, requires, reads, scope="current query hypothesis",
              mechanism="guarded_semantic_derivation", sources=LOCAL, notes="", operation="add"):
    c.add(key, typ, definition, family, value=value, scope=scope,
          head=f"Derive {key.replace('_', ' ')}", function=definition, mechanism=mechanism,
          contract={"match": {"domain": "visible_prefix", "bind": condition},
                    "guards": ["all source indices <= query index", "all source annotations are themselves prefix-causal",
                               "keep entity/event/scope and source provenance attached to alternatives"],
                    "emit": {key: transform}, "abstain": "missing premises, inaccessible scope, or unresolved incompatible bindings"},
          requires=requires, reads=reads, sources=sources,
          positive=example(positive, {key: value}, condition),
          negative=example(negative, {}, "The contrasting prefix fails a premise; do not infer the positive value."),
          operation=operation, notes=notes or "Proposed contract; no implementation or learned accuracy is claimed.")


def _identity(c):
    f = "identity_annotation"
    _lookup(c, "lemma", "string", "Canonical lexical base form of this word occurrence after its intended inflectional analysis is selected.", f,
            {"scissors": "scissors", "rabbits": "rabbit", "took": "take", "needles": "needle"})
    _lookup(c, "pos", "string", "Compact annotation word class; n includes common and proper nouns and does not identify a semantic role.", f,
            {"scissors": "n", "the": "det", "quickly": "adv", "and": "conj"})
    _lookup(c, "entity", "string", "Canonical annotation entity label or category such as scissors or girl; it is not an entity identifier.", f,
            {"scissors": "scissors", "needle": "needle", "rabbit": "rabbit"}, field="lemma", tests={"pos": "n"})
    _contract(c, "entity_id", "entity_ref", "Stable eN identifier assigned to a discourse referent from an introduction or a resolved preceding reference.", f, "e1",
              condition="Bind current referring mention q and one accessible earlier mention a that is independently established as the same referent.",
              transform={"copy": "a.entity_id"}, positive=[{"token": "Lily", "entity_id": "e1"}, {"token": "returned"}, {"token": "."}, {"token": "that"}, {"token": "same"}, {"token": "Lily"}],
              negative=[{"token": "Lily", "entity_id": "e1"}, {"token": "another"}, {"token": "Lily"}],
              requires=["reference_resolution", "scope_accessibility", "fresh_id_allocation"], reads=["token", "entity_id", "scope_id"])
    _carry(c, "entity_name", "string", "Canonical surface name for this resolved entity, preserving identity across a new adjacent mention.", f, "Lily")
    _carry(c, "event", "string", "Shared concise event label attached to mentions of one identified event, such as obtain object; not a complete future purpose.", f, "obtain object", identity="event_id", scope="event mention")
    _contract(c, "event_id", "string", "Stable evN identifier linking a predicate and the participants already attached to that event in the visible prefix.", f, "ev3",
              condition="Bind predicate p with event_id and current participant q whose parsed attachment targets p; keep the governing event scope.",
              transform={"copy": "p.event_id"}, positive=[{"token": "took", "event_id": "ev3"}, {"token": "scissors", "role": "patient"}],
              negative=[{"token": "took", "event_id": "ev3"}, {"token": "."}, {"token": "scissors"}],
              requires=["predicate_attachment", "event_scope"], reads=["event_id", "role", "clause_id"])
    _lookup(c, "event_type", "string", "Coarse event category used by the annotation schema, derived from an already disambiguated event label.", f,
            {"obtain object": "obtain", "repair object": "repair", "move object": "move", "say words": "speak"}, field="event")
    _native(c, "actor", "string", "Canonical name of an already resolved acting entity for the current event; a display label alongside actor_id.", f, "Lily",
            seq(gap(), tok("person", entity_id=present(), entity_name=present()), tok(actor_id=ref("person.entity_id"))),
            ref("person.entity_name"), [{"token": "Lily", "entity_id": "e1", "entity_name": "Lily"}, {"token": "took", "actor_id": "e1"}],
            [{"token": "Lily", "entity_id": "e1", "entity_name": "Lily"}, {"token": "took", "actor_id": "e2"}], mechanism="role_bound_name_copy")
    _carry(c, "actor_id", "entity_ref", "Entity identifier of the semantic actor carried between adjacent mentions of the same event and scope.", f, "e1", identity="event_id", scope="event role")
    _carry(c, "recipient_id", "entity_ref", "Entity identifier of the already identified recipient of this event; not an arbitrary nearby person.", f, "e2", identity="event_id", scope="event role")
    _contract(c, "role", "string", "Semantic role of the current mention in its identified event, using the existing compact role vocabulary.", f, "patient",
              condition="Bind a resolved event frame and current participant q; select the frame slot filled by q rather than equating every grammatical object with a patient.",
              transform={"map": "frame.slot(q)", "to": "compact_role"}, positive=[{"token": "cut", "event_type": "other"}, {"token": "paper"}],
              negative=[{"token": "weighed", "event_type": "state"}, {"token": "three"}, {"token": "pounds"}],
              requires=["frame_slot_binding"], reads=["event_id", "event_type", "entity_id"], sources=(*LOCAL, "framenet"))
    _carry(c, "factuality", "string", "Annotation event status: asserted, negated, desired, hypothetical or reported, preserved within one event and scope.", f, "reported", identity="event_id", scope="event assertion")
    _contract(c, "location", "string", "Legacy display-name field for an entity's known holder or place, materialized only from the relevant scoped location relation.", f, "Lily",
              condition="Bind current entity q and most recent applicable asserted location/holder relation r; resolve r.destination to a known canonical entity name.",
              transform={"lookup_entity_name": "r.destination"}, positive=[{"token": "Lily", "entity_id": "e1", "entity_name": "Lily"}, {"token": "holds"}, {"token": "scissors", "entity_id": "e3"}],
              negative=[{"token": "Lily", "entity_id": "e1", "entity_name": "Lily"}, {"token": "wants"}, {"token": "scissors", "entity_id": "e3"}],
              requires=["relation_extraction", "scoped_latest_state", "entity_name_lookup"], reads=["entity_id", "entity_name", "factuality"], scope="entity location display")
    for key, role in [("patients", "patient"), ("instruments", "instrument")]:
        _contract(c, key, "array", f"Canonical names of already introduced {role} participants of this event; future participants remain absent until mentioned.", f, ["paper" if role == "patient" else "scissors"],
                  condition=f"Bind event e and every accessible prefix mention p explicitly attached to e with semantic role {role}; deduplicate by entity identity.",
                  transform={"collect": "p.entity_name", "distinct_by": "p.entity_id"},
                  positive=[{"token": "cut", "event_id": "ev1"}, {"token": "paper" if role == "patient" else "scissors", "entity_name": "paper" if role == "patient" else "scissors", "role": role, "event_id": "ev1"}],
                  negative=[{"token": "cut", "event_id": "ev1"}], requires=["event_participant_collection"], reads=["event_id", "entity_id", "entity_name", "role"])
    _carry(c, "attributes", "array", "Legacy annotation list of name/string-value pairs for one entity; typed catalog fields remain separate rather than changing this wire format.", f, [{"name": "color", "value": "red"}])
    _contract(c, "scope_id", "string", "Identifier of the current assertion, quotation, conditional or modal scope in which semantic evidence is interpreted.", f, "s2",
              condition="Parse visible scope-opening and scope-closing constructions; bind the innermost live scope at the query.", transform={"copy": "scope_stack.top.id"},
              positive=[{"token": "if"}, {"token": "rain"}], negative=[{"token": "rain"}],
              requires=["incremental_scope_stack"], reads=["token", "clause_id"], sources=(*LOCAL, "codeco"))
    _lookup(c, "assertion_status", "string", "How a proposition is being presented at this mention, preserving quotation/question status separately from whether its event is true.", f,
            {"allegedly": "attributed_claim", "reportedly": "attributed_claim", "suppose": "introduced_assumption"}, notes="This cue interpretation never implies that all subsequent text shares the status; scope assignment is separate.")
    _contract(c, "evidence_source_id", "string", "Identifier of the report, perception, derivation or annotation source supporting the current semantic claim.", f, "src1",
              condition="Bind a current claim and the explicit reporting/perception record that introduced it, keeping source identity separate from the claim's actor.", transform={"copy": "support.source_id"},
              positive=[{"token": "Lily"}, {"token": "reported"}, {"token": "rain"}], negative=[{"token": "rain"}],
              requires=["claim_source_linking", "source_id_allocation"], reads=["event_id", "actor_id", "scope_id"])
    _lookup(c, "lexical_sense_id", "string", "Candidate sense identifier for an explicit lexical disambiguation, independent of a particular discourse entity.", f,
            {"scissors": "scissors.n.01", "rabbit": "rabbit.n.01"}, field="lemma", tests={"pos": "n"}, sources=("wordnet", "local.storyformer"),
            notes="Authored sense candidates only, not exhaustive WSD; ambiguous alternatives must remain available.")
    _lookup(c, "ontological_type", "string", "Broad semantic kind of a selected lexical sense; this is type evidence and never proof that an entity exists in the story.", f,
            {"scissors.n.01": "artifact", "rabbit.n.01": "organism"}, field="lexical_sense_id", sources=("wordnet",))
    _lookup(c, "referent_kind", "string", "Kind of referent denoted by the expression: individual, group, event, proposition or kind, after semantic resolution.", f,
            {"someone": "individual", "everyone": "quantified_set", "something": "unspecified_individual"}, notes="Lexical seeds give denotation candidates, not entity creation or existential commitment.")
    _lookup(c, "mention_form", "string", "Surface reference strategy of this mention, kept separate from the identity to which it may resolve.", f,
            {"she": "personal_pronoun", "he": "personal_pronoun", "this": "demonstrative", "herself": "reflexive"})
    _contract(c, "alias_names", "array", "Explicitly licensed alternative names for the same referent; identical names alone do not merge entities.", f, ["Mira", "Captain Reed"],
              condition="Bind an explicit same-person naming construction with two names and one established referent.", transform={"union_distinct": ["current_aliases", "new_name"]},
              positive=[{"token": "Mira"}, {"token": "also"}, {"token": "called"}, {"token": "Captain Reed"}],
              negative=[{"token": "Mira"}, {"token": "met"}, {"token": "Captain Reed"}], requires=["naming_construction_parse", "set_union"], reads=["entity_id", "entity_name"])
    _contract(c, "naming_event_id", "string", "Event identifier for the explicit naming or renaming that licenses the current display name.", f, "ev2",
              condition="Bind completed naming event e, its named entity and new name, with assertion status and temporal applicability.", transform={"copy": "e.event_id"},
              positive=[{"token": "named", "event_id": "ev2"}, {"token": "boat"}, {"token": "Dawn"}], negative=[{"token": "dreamed"}, {"token": "Dawn"}],
              requires=["naming_frame_binding"], reads=["event_id", "entity_id", "factuality"])
    _contract(c, "identity_hypothesis", "object", "Candidate identity link with source mention, antecedent entity and scope, retaining alternatives instead of silently merging them.", f, {"mention": 4, "entity_id": "e1", "scope_id": "s1"},
              condition="Bind current referential mention q and compatible accessible antecedent a; emit one hypothesis per compatible binding.", transform={"record": {"mention": "q.index", "entity_id": "a.entity_id", "scope_id": "q.scope_id"}},
              positive=[{"token": "Lily", "entity_id": "e1"}, {"token": "she", "index": 4, "scope_id": "s1"}], negative=[{"token": "a"}, {"token": "new"}, {"token": "girl", "index": 4}],
              requires=["scope_accessibility", "referential_compatibility"], reads=["entity_id", "index", "scope_id"], sources=(*LOCAL, "codeco"))
    _contract(c, "entity_merge_candidate", "object", "Explicit evidence proposing two previously distinct referent IDs denote one entity; acceptance must preserve provenance.", f, {"left": "e1", "right": "e2", "basis": "explicit_identity"},
              condition="Bind an asserted identity statement between two known individual referents, excluding similarity and role predication.", transform={"record": {"left": "a.entity_id", "right": "b.entity_id", "basis": "explicit_identity"}},
              positive=[{"token": "Mira", "entity_id": "e1"}, {"token": "is"}, {"token": "Captain Reed", "entity_id": "e2"}], negative=[{"token": "Mira", "entity_id": "e1"}, {"token": "resembles"}, {"token": "Captain Reed", "entity_id": "e2"}],
              requires=["identity_vs_predication_disambiguation"], reads=["entity_id", "factuality"])
    _contract(c, "entity_split_candidate", "object", "Evidence that one provisional discourse identity must be separated into two referents, without rewriting prior causal records.", f, {"old": "e1", "new_mention": 5, "basis": "different_individual"},
              condition="Bind a contrastive other/different-person construction contradicting a prior provisional identity assignment.", transform={"record": {"old": "a.entity_id", "new_mention": "q.index", "basis": "different_individual"}},
              positive=[{"token": "Lily", "entity_id": "e1"}, {"token": "another"}, {"token": "Lily", "index": 5}], negative=[{"token": "Lily", "entity_id": "e1"}, {"token": "again"}],
              requires=["identity_conflict_detection", "fresh_id_allocation"], reads=["entity_id", "index"])
    _contract(c, "generic_reference", "boolean", "Whether the current nominal is interpreted as a kind-level generic claim rather than a particular individual in the scene.", f, True,
              condition="Resolve nominal and predicate jointly as a generic statement with no individual episode anchor; retain a generic alternative if ambiguous.", transform={"literal": True},
              positive=[{"token": "Birds"}, {"token": "have"}, {"token": "wings"}], negative=[{"token": "Birds"}, {"token": "landed"}, {"token": "yesterday"}],
              requires=["genericity_resolution"], reads=["token", "event_type", "scope_id"])
    _contract(c, "group_members", "array", "Identifiers of entities explicitly included in the current discourse group; group identity and individual identities remain distinct.", f, ["e1", "e2"],
              condition="Bind a resolved coordinated or enumerated group and all explicitly introduced conjunct referents in that group.", transform={"collect_distinct": "members.entity_id"},
              positive=[{"token": "Lily", "entity_id": "e1"}, {"token": "and"}, {"token": "Ben", "entity_id": "e2"}], negative=[{"token": "Lily", "entity_id": "e1"}, {"token": "or"}, {"token": "Ben", "entity_id": "e2"}],
              requires=["group_construction_parse", "set_collection"], reads=["entity_id", "scope_id"])
    _contract(c, "speaker_local_name", "object", "Speaker-specific name for an entity, allowing a nickname or mistaken name without changing the narrator's canonical entity name.", f, {"speaker_id": "e1", "entity_id": "e2", "name": "Captain"},
              condition="Bind quoted vocative/naming use to its speaker and intended entity under the quote's scope.", transform={"record": {"speaker_id": "speaker.entity_id", "entity_id": "addressee.entity_id", "name": "name.surface"}},
              positive=[{"token": "Lily", "entity_id": "e1"}, {"token": "said"}, {"token": "Captain"}], negative=[{"token": "a"}, {"token": "captain"}, {"token": "arrived"}],
              requires=["quotation_attribution", "vocative_resolution"], reads=["entity_id", "scope_id", "surface"])


def _words(text):
    """Human-authored contract illustration, not an automatic semantic annotator."""
    return [{"token": token} for token in text.split()]


def _design(c, family, key, typ, description, value, good, bad, condition, transform,
            capability, *, reads=("token", "entity_id", "event_id", "scope_id"), sources=LOCAL,
            mechanism="guarded_semantic_derivation", scope="current query hypothesis"):
    _contract(c, key, typ, description, family, value, condition=condition,
              transform=transform if isinstance(transform, dict) else {"derive": transform},
              positive=_words(good), negative=_words(bad), requires=[capability],
              reads=reads, sources=sources, mechanism=mechanism, scope=scope,
              notes="The text-only examples illustrate the intended interpretation. IDs in expected bundles are schematic adapter allocations; an implementation must ground them to the prefix and retain ambiguity.")


def _reference(c):
    f = "reference_resolution"
    rows = [
        ("antecedent_id", "entity_ref", "Entity chosen as the accessible antecedent of the current anaphor, with ambiguity retained before choosing.", "e1", "Lily smiled . She", "Lily smiled . Another girl", "Resolve a personal anaphor against compatible accessible antecedents; do not equate a new indefinite with an antecedent.", "selected_antecedent.entity_id", "accessible_antecedent_selection"),
        ("antecedent_candidates", "array", "All currently compatible accessible referent IDs for an unresolved anaphor; absence of a candidate is not negation of existence.", ["e1", "e2"], "Lily met Mira . She", "Lily met Mira . A third girl", "Collect antecedents compatible with reference form and local scope; preserve a tie between Lily and Mira.", "compatible_accessible_ids", "antecedent_candidate_collection"),
        ("antecedent_mention_index", "number", "Position of the particular earlier mention supplying a reference link, distinct from the entity identifier.", 0, "Lily waved . She", "She waved . Lily", "Choose an earlier accessible mention supporting the resolved current pronoun; later Lily cannot license earlier She.", "antecedent.index", "mention_link_resolution"),
        ("reference_chain_id", "string", "Identity of the discourse mention chain to which a new resolved mention attaches, independent of surface spelling.", "rc1", "a rabbit appeared . the rabbit", "a rabbit appeared . another rabbit", "Attach a definite repeat to the established chain only after same-referent resolution.", "antecedent.chain_id", "reference_chain_linking"),
        ("reference_distance", "number", "Number of word/punctuation records between a resolved anaphor and its selected antecedent mention.", 2, "Lily smiled . She", "Lily smiled . Someone", "After selecting an antecedent, subtract its index from query index and exclude both endpoints.", "query.index - antecedent.index - 1", "index_arithmetic"),
        ("referent_accessible", "boolean", "Whether a particular earlier referent is accessible from the current discourse scope, rather than merely present in the window.", True, "Lily found a key . The key", "Lily did not find a key . The key", "Apply discourse accessibility rules to the candidate antecedent's introducing scope and current scope.", True, "discourse_accessibility"),
        ("reference_introduction", "boolean", "Whether this mention introduces a new discourse referent under its current scope, including hypothetical introductions.", True, "Lily found a rabbit", "Lily found the same rabbit", "Recognize an introducing indefinite rather than a resolved same-reference definite; do not assert actual existence outside scope.", True, "referent_introduction_parse"),
        ("reference_reactivation", "boolean", "A new mention returns attention to an already introduced but interveningly inactive discourse referent.", True, "Lily saw Ben . Mira spoke . Ben", "Lily saw Ben . Another boy", "Resolve the current mention to an older referent and observe an intervening focus change.", True, "discourse_focus_history"),
        ("reference_unresolved", "boolean", "The current expression requires reference resolution but the visible prefix supplies no unique supported binding.", True, "Lily met Mira . She", "Lily was alone . She", "Evaluate accessible candidates and mark unresolved when several remain rather than selecting a name by recency alone.", True, "reference_ambiguity_test"),
        ("reference_competitor_ids", "array", "Non-selected but still plausible antecedents for the current reference, useful for calibrated suppression or alternative bundles.", ["e2"], "Lily and Mira waited . She", "Lily waited alone . She", "Keep alternative compatible referents after a tentative preferred binding; do not include inaccessible entities.", "candidates minus preferred", "candidate_set_difference"),
        ("reference_excluded_ids", "array", "Antecedents rejected by an explicit binding or identity constraint, with exclusion scoped to the current reference.", ["e1"], "Lily blamed her", "Lily blamed herself", "Apply local nonreflexive versus reflexive binding constraints; exclude the local subject only under the relevant nonreflexive interpretation.", "locally_forbidden_antecedent_ids", "syntactic_binding_filter"),
        ("deictic_anchor_id", "entity_ref", "Contextually established object or person serving as the anchor of a demonstrative use, not a guessed visually salient entity.", "e2", "Lily pointed at the cup . This", "Lily mentioned a cup . This", "Bind a demonstrative to a preceding explicit pointing/presentation anchor when discourse evidence uniquely licenses it.", "pointed_target.entity_id", "deictic_reference_linking"),
        ("deictic_distance_class", "string", "Near/far contrast encoded by a demonstrative relative to its discourse speaker, without an inferred metric distance.", "proximal", "this cup", "the cup", "Recognize a proximal demonstrative governing the current nominal and preserve the speaker frame.", "proximal", "demonstrative_attachment"),
        ("bridging_relation", "object", "Relation licensing an indirectly introduced definite referent, such as a handle belonging to a previously mentioned door.", {"anchor": "e1", "relation": "part_of"}, "Lily found a door . The handle", "Lily found a door . A cloud", "Resolve a definite part noun through an appropriate earlier whole, while preserving alternative anchors.", "{anchor: whole.entity_id, relation: part_of}", "bridging_reference_inference"),
        ("associative_antecedent_id", "entity_ref", "Anchor entity for an associated group expression such as the captain's crew, distinct from same-entity coreference.", "e1", "The captain arrived . Her crew", "The captain arrived . She", "Bind an associative group to its named anchor without merging group and individual identities.", "anchor.entity_id", "associative_reference_resolution"),
        ("split_antecedent_ids", "array", "Several separately introduced entities jointly serving as antecedents of a plural pronoun.", ["e1", "e2"], "Lily arrived . Ben followed . They", "Lily arrived . Ben followed . He", "Resolve a plural pronoun to a discourse group composed of distinct compatible introduced individuals.", "selected_individual_ids", "split_antecedent_resolution"),
        ("reciprocal_participant_ids", "array", "Participants licensed by a reciprocal expression, preserving that reciprocal roles may have several pairings.", ["e1", "e2"], "Lily and Ben helped each other", "Lily helped herself", "Bind reciprocal expression to the local plural antecedent; do not treat reflexivity as reciprocity.", "plural_antecedent.members", "reciprocal_binding"),
        ("reflexive_antecedent_id", "entity_ref", "Locally licensed antecedent of a reflexive expression, determined by binding domain rather than nearest noun.", "e1", "Lily showed Ben herself", "Lily showed Ben her", "Select the reflexive's structurally permitted antecedent in the current clause/binding domain.", "local_binder.entity_id", "reflexive_binding"),
        ("logophoric_center_id", "entity_ref", "Perspective holder licensing an exempt or logophoric anaphor, distinguished from ordinary local grammatical binding.", "e1", "Lily felt that the picture of herself was odd", "Lily saw a picture of a stranger", "Resolve a perspective-sensitive reflexive only when the text establishes the relevant center; retain ambiguity.", "perspective_holder.entity_id", "logophoric_resolution"),
        ("cataphoric_pending", "boolean", "A referential expression currently lacks a preceding antecedent and may await later resolution; it must remain unresolved in this prefix.", True, "Before she arrived", "Lily arrived . She", "Detect an unresolved pronoun in a fronted subordinate construction, without filling it from future tokens.", True, "pending_reference_state"),
        ("expletive_reference", "boolean", "A grammatical pronoun is nonreferential under the current construction, such as weather it or existential there.", True, "It is raining", "It is broken", "Disambiguate the completed weather/expletive construction from an ordinary referring pronoun.", True, "expletive_construction_parse"),
        ("propositional_antecedent_id", "string", "Identifier of the prior proposition referred to by this/that/so, rather than an object or entity with the same words.", "p1", "Lily left . That surprised Ben", "Lily left . That cup", "Resolve a demonstrative in a proposition-selecting predicate to a prior scoped proposition.", "antecedent.proposition_id", "propositional_anaphora"),
        ("event_antecedent_id", "string", "Prior event selected by event anaphora such as doing that or the accident, keeping its own factuality.", "ev1", "Lily jumped . Ben did that too", "Lily had a hat . Ben wore that", "Bind the anaphoric event expression to a compatible accessible event, not a nominal object.", "antecedent.event_id", "event_anaphora"),
        ("kind_antecedent_id", "string", "Previously introduced kind referenced by one/ones or another of that kind, without copying the original individual's identity.", "kind_rabbit", "Lily saw a rabbit . Ben saw another one", "Lily saw a rabbit . Ben saw it", "Resolve one-anaphora to nominal kind while allocating a distinct individual where licensed.", "antecedent.kind_id", "one_anaphora_resolution"),
        ("donkey_reference", "object", "Bound-variable interpretation of a dependent pronoun across a conditional or quantified construction, not one global entity.", {"binder": "v_key", "scope": "s_if"}, "If a child finds a key the child keeps it", "A child found a key . It", "Retain the pronoun's dependence on the conditional indefinite; do not assign a universal fixed eN identity.", "{binder: indefinite.variable, scope: conditional.id}", "dynamic_binding"),
        ("reference_presupposition", "object", "Existence/uniqueness/familiarity requirement introduced by a referential form, recorded as a requirement rather than an asserted fact.", {"kind": "unique_referent", "description": "key"}, "Lily picked up the key", "Lily picked up a key", "Extract the definite description's contextual identification requirement and its descriptive restriction.", "definite_identification_requirement", "presupposition_extraction"),
        ("reference_accommodation", "object", "Tentative introduction of a referent needed to satisfy a definite expression when prior evidence is incomplete, explicitly marked defeasible.", {"description": "door", "status": "accommodated"}, "Lily entered . The door closed", "Lily entered . A door closed", "Propose a discourse accommodation for the definite door; do not present it as an earlier observed entity.", "{description: nominal.restriction, status: accommodated}", "reference_accommodation"),
        ("reference_specificity", "string", "Whether a nominal is intended to identify a particular individual or permits a nonspecific witness within its scope.", "nonspecific", "Lily needs any key that works", "Lily needs this particular key", "Resolve specificity from determiners and modal context, retaining ambiguity for ordinary a-key expressions.", "nonspecific", "specificity_resolution"),
        ("reference_uniqueness_domain", "object", "Contextual domain within which a definite description claims uniqueness, such as a particular room rather than the whole world.", {"domain": "room1", "restriction": "window"}, "In this room the window", "In every room a window", "Bind definite uniqueness to the explicitly established local domain and descriptive restriction.", "{domain: local_domain.id, restriction: nominal.restriction}", "domain_restriction"),
        ("reference_quotation_shift", "object", "A first/second-person reference interpreted under an explicit quoted speaker/addressee frame rather than the narrator frame.", {"form": "I", "entity_id": "e1"}, "Lily said : I", "Lily mentioned the letter I", "Bind quoted I to the attributed speaker only in a speech-content scope; exclude mention of the word itself.", "{form: query.token, entity_id: quote.speaker_id}", "quotation_deixis"),
        ("reference_metonymic_link", "object", "Contextual relation between a literal referent and the intended related participant, such as a building for its staff.", {"literal": "e1", "relation": "institution_staff"}, "The school announced a holiday", "The school had a red roof", "Propose an institution-for-staff interpretation under a speech predicate without replacing the building's identity.", "{literal: subject.entity_id, relation: institution_staff}", "metonymy_resolution"),
        ("reference_identity_conflict", "object", "Two current identity constraints cannot be jointly satisfied by one referent, requiring alternatives or an explicit correction.", {"left": "e1", "right": "e2", "constraint": "distinct"}, "Lily and a different Lily arrived", "Lily also called Lily arrived", "Detect an explicit distinctness constraint against a proposed same-name merge.", "{left: prior.id, right: new.id, constraint: distinct}", "identity_constraint_consistency"),
    ]
    for row in rows:
        _design(c, f, *row, sources=(*LOCAL, "codeco", "ace"), mechanism="scoped_reference_binding")


def _temporal(c):
    f = "temporal_semantics"
    lexical = [
        ("temporal_signal_relation", "Temporal relation suggested by this connective, before both related event arguments are necessarily filled.", {"before": "before", "after": "after", "during": "overlap", "until": "upper_bound"}),
        ("temporal_deixis", "Relative time orientation of a deictic time expression with respect to its yet-to-be-resolved anchor.", {"yesterday": "previous_day", "today": "current_day", "tomorrow": "next_day", "now": "anchor_present"}),
        ("temporal_granularity", "Named scale of a temporal unit expression, without inventing its length or occurrence time.", {"second": "second", "minute": "minute", "hour": "hour", "day": "day", "year": "year"}),
        ("temporal_frequency_class", "Qualitative recurrence cue expressed by the current adverb, distinct from a measured event frequency.", {"always": "universal", "often": "high", "sometimes": "occasional", "never": "zero"}),
        ("temporal_phase_cue", "Phase boundary evoked by a lexical aspectual verb; its complement event and assertion status still require binding.", {"began": "onset", "continued": "continuation", "stopped": "cessation", "finished": "completion"}),
        ("temporal_order_cue", "Discourse ordering instruction from a temporal adverb, not proof that the narrated order matches event chronology.", {"previously": "earlier", "subsequently": "later", "meanwhile": "overlap", "afterward": "later"}),
        ("temporal_bound_cue", "Boundary type introduced by a time-marking preposition before the bounded interval is fully known.", {"since": "lower_bound", "until": "upper_bound", "throughout": "whole_interval"}),
        ("calendar_day_name", "Weekday name explicitly present in the text; absolute date requires an anchor and calendar convention.", {"Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday", "Thursday": "Thursday", "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday"}),
    ]
    for key, desc, mapping in lexical:
        _lookup(c, key, "string", desc, f, mapping, sources=("timeml",), scope="temporal expression cue")
    rows = [
        ("time_expression_id", "string", "Identifier for a fully recognized time expression span, kept separate from the event it modifies.", "t1", "Lily waited until noon", "Lily waited until Ben arrived", "Recognize a completed nominal clock-time expression rather than an event clause and allocate its time-expression ID.", "time_span.id", "time_expression_recognition"),
        ("time_anchor_id", "string", "Reference time against which a relative temporal expression is interpreted, including quote-local and narrative anchors.", "t0", "On Monday Lily said tomorrow", "Lily said tomorrow", "Resolve tomorrow against the explicitly provided reporting-time anchor without assuming the machine date.", "resolved_anchor.id", "temporal_anchor_resolution"),
        ("event_time_interval", "object", "Scoped temporal interval assigned to an event, preserving its day/clock anchors and factuality without guessing an absolute date or time zone.", {"event": "ev1", "start": "10:00", "end": "11:00", "clock": "local_24_hour", "day_anchor": "t_day1", "factuality": "asserted", "scope_id": "s1"}, "On that Monday Lily waited from ten a.m. to eleven a.m. local time", "Lily might wait sometime", "Attach both explicit morning endpoints to the same asserted waiting event and the stated local Monday anchor; its absolute date and time zone remain unresolved.", "{event:e.id,start:start_time,end:end_time,clock:clock_convention,day_anchor:day.id,factuality:e.factuality,scope_id:e.scope_id}", "event_interval_binding"),
        ("event_time_relation", "object", "Directed relation between two identified event intervals; the endpoints and relation travel together.", {"left": "ev1", "relation": "before", "right": "ev2"}, "Lily left before Ben arrived", "Lily left because Ben arrived", "Bind the two completed event arguments of before; causality alone does not determine an exact temporal relation.", "{left: matrix.id, relation: before, right: subordinate.id}", "temporal_relation_extraction"),
        ("temporal_duration", "object", "Explicit event duration as magnitude and unit, independent of the event's absolute beginning.", {"value": 2, "unit": "hour"}, "Lily waited for two hours", "Lily waited at two", "Recognize a durative measure attached to the event rather than a clock time.", "{value: measure.value, unit: measure.unit}", "duration_parse"),
        ("temporal_start_bound", "object", "Known lower boundary of an event interval, with inclusive/exclusive and anchor information when available.", {"event": "ev1", "time": "noon"}, "Lily waited from noon", "Lily waited until noon", "Attach a from/since boundary as the start of the relevant event interval.", "{event: e.id, time: bound.id}", "interval_boundary_binding"),
        ("temporal_end_bound", "object", "Known upper boundary of an event interval, without conflating an intended deadline with observed completion.", {"event": "ev1", "time": "noon"}, "Lily waited until noon", "Lily wanted to finish by noon", "Bind the upper boundary of an asserted waiting interval; keep deadline obligations in their separate field.", "{event: e.id, time: bound.id}", "interval_boundary_binding"),
        ("temporal_deadline", "object", "Time by which a planned or obligated event should finish, explicitly not evidence that it actually finished.", {"event": "ev1", "by": "noon", "status": "required"}, "Lily must return by noon", "Lily returned at noon", "Bind a by-time constraint to a modal/required event.", "{event: e.id, by: t.id, status: required}", "deadline_scope_binding"),
        ("temporal_elapsed", "object", "Elapsed duration between a known start and a current anchored observation.", {"value": 2, "unit": "hour"}, "Lily started at ten a.m. today . It is now noon on the same local clock", "Lily may start at ten a.m. today . It is now noon", "Subtract compatible times only when the start event is asserted and both times share the same explicit day and clock frame.", "current_time - start_time", "time_arithmetic"),
        ("temporal_remaining", "object", "Remaining duration until a known future boundary from a resolved current time.", {"value": 1, "unit": "hour"}, "It is eleven a.m. . The bell is scheduled for noon today on the same local clock", "It is eleven a.m. . A bell rang yesterday", "Resolve both times on one explicit day/clock frame and subtract current time from the relevant future bound; a schedule is not proof of eventual ringing.", "future_bound - current_time", "time_arithmetic"),
        ("temporal_recurrence", "object", "Explicit recurrence schedule for an event type, with period and scope, distinct from observed instance count.", {"period": 1, "unit": "day"}, "Lily waters flowers every day", "Lily watered flowers that day", "Bind distributive temporal quantification to the event template.", "{period: 1, unit: day}", "recurrence_parse"),
        ("temporal_iteration_index", "number", "Ordinal number of an explicitly ordered occurrence of an event in its local sequence.", 3, "For the third time Lily knocked", "Lily knocked three times", "Distinguish an ordinal occurrence from a cardinal total count of knocks.", "ordinal.value", "iteration_index_binding"),
        ("temporal_iteration_count", "number", "Total number of explicitly asserted occurrences in an event repetition phrase.", 3, "Lily knocked three times", "Lily knocked for the third time", "Bind the cardinal times expression to the completed repeated event.", "count.value", "event_count_binding"),
        ("temporal_overlap", "object", "Evidence that two scoped event intervals share time, without assuming identical starts or ends.", {"events": ["ev1", "ev2"], "relation": "overlap"}, "While Lily cooked Ben sang", "After Lily cooked Ben sang", "Bind a temporal while construction and retain both interval IDs.", "{events: [e1.id,e2.id], relation: overlap}", "interval_relation_binding"),
        ("temporal_containment", "object", "One event interval is contained in a named interval, preserving interval identity and direction.", {"inner": "ev1", "outer": "t1"}, "Lily slept during the journey", "Lily slept after the journey", "Resolve during as temporal containment where the context supports it, rather than loose topic association.", "{inner: event.id, outer: interval.id}", "interval_containment"),
        ("temporal_simultaneity", "object", "Explicit synchronization of two events to the same relevant time point or interval.", {"events": ["ev1", "ev2"], "relation": "simultaneous"}, "Lily and Ben arrived at the same moment", "Lily and Ben arrived that day", "Require explicit same-moment synchronization; sharing a broad date is insufficient.", "{events: events.ids, relation: simultaneous}", "synchrony_binding"),
        ("temporal_sequence_gap", "object", "Explicit gap duration between the end of one event and beginning of another.", {"left": "ev1", "right": "ev2", "gap": 2, "unit": "hour"}, "Two hours after Lily left Ben arrived", "After Lily left Ben arrived", "Resolve the duration modifier of an after relation between two events.", "{left: e1.id,right:e2.id,gap:d.value,unit:d.unit}", "relative_time_composition"),
        ("temporal_uncertainty", "object", "Explicitly uncertain temporal interval or relation, retaining bounds rather than inventing a precise timestamp.", {"around": "noon", "precision": "approximate"}, "Lily arrived around noon", "Lily arrived exactly at noon", "Bind approximation to the time expression and preserve its qualitative uncertainty.", "{around:t.value,precision:approximate}", "temporal_modifier_scope"),
        ("temporal_alternative_set", "array", "Disjunctive candidate times expressed by the text; alternatives are not simultaneous events.", ["Monday", "Tuesday"], "Lily will arrive Monday or Tuesday", "Lily will arrive Monday and leave Tuesday", "Bind coordinated alternatives to one event's time slot, excluding separate event predicates.", "time_alternatives", "temporal_disjunction"),
        ("temporal_reference_shift", "object", "An explicitly established new narrative reference time against which subsequent temporal relations may be interpreted.", {"from": "t1", "to": "t2"}, "Years later Lily returned", "Lily remembered years earlier", "Recognize a narrative frame shift rather than an embedded memory-time expression.", "{from:prior_anchor.id,to:new_anchor.id}", "narrative_time_update"),
        ("temporal_persistence_window", "object", "Interval over which a stated condition is explicitly said to hold; no indefinite persistence is assumed.", {"state": "door_closed", "until": "dawn"}, "The door stayed closed until dawn", "The door was closed once", "Bind a persistence predicate and its explicit boundary to one state assertion.", "{state:s.id,until:t.id}", "state_duration_binding"),
        ("temporal_order_conflict", "object", "Two supported temporal constraints cannot both hold under the same event identities and timeline.", {"left": "ev1", "right": "ev2", "conflict": "strict_cycle"}, "Lily left before Ben arrived . Ben arrived before Lily left", "Lily left before Ben arrived . Ben ate before Lily slept", "Detect a strict before cycle after confirming matching event identities and scope.", "minimal_inconsistent_temporal_cycle", "temporal_constraint_consistency"),
        ("temporal_anchor_unresolved", "boolean", "A relative temporal expression is understood but its absolute or story-local anchor remains unspecified in the prefix.", True, "Tomorrow Lily leaves", "Today is Monday . Tomorrow Lily leaves", "Detect absence of a licensed anchor for a deictic expression without substituting the system date.", True, "temporal_anchor_missing_test"),
        ("temporal_calendar_context", "object", "Explicit calendar/year/timezone convention needed to normalize a date; unspecified components remain unknown.", {"year": 2024, "calendar": "Gregorian"}, "In the Gregorian year 2024 on March first", "On March first", "Extract only explicitly established calendar context and attach it to the current date expression.", "explicit_calendar_components", "calendar_context_resolution"),
    ]
    for row in rows:
        _design(c, f, *row, sources=("timeml", "local.storyformer"), mechanism="temporal_relation_composition")


def _quantity(c):
    f = "quantity_measurement"
    _lookup(c, "cardinal_value", "number", "Numeric value of an explicitly recognized cardinal numeral, independent of any measured entity.", f,
            {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "ten": 10})
    _lookup(c, "ordinal_rank", "number", "One-based rank explicitly encoded by an ordinal expression; it does not establish the size of the ordered set.", f,
            {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5})
    _lookup(c, "measure_dimension", "string", "Physical dimension suggested by an unambiguous unit sense, before a full numeric measure is assembled.", f,
            {"liters": "volume", "kilograms": "mass", "centimeters": "length", "seconds": "time"})
    _lookup(c, "measure_unit", "string", "Canonical unit symbol for the current explicitly written unit, preserving unit identity for later dimensional checks.", f,
            {"liters": "L", "kilograms": "kg", "centimeters": "cm", "seconds": "s"})
    _lookup(c, "quantity_comparison_cue", "string", "Comparison direction evoked by a quantitative word; operands and domain must still be bound.", f,
            {"more": "greater", "less": "smaller_mass_or_degree", "fewer": "smaller_count", "equal": "equal"})
    _lookup(c, "quantity_approximation_cue", "string", "Approximation operator expressed by the current modifier, not a numerically specified uncertainty interval.", f,
            {"about": "approximate", "roughly": "approximate", "exactly": "exact", "nearly": "below_near"})
    _lookup(c, "quantity_distribution_cue", "string", "Distributive force of a count expression over individuals or groups, awaiting a resolved distribution domain.", f,
            {"each": "per_individual", "apiece": "per_individual", "together": "collective"})
    _lookup(c, "quantity_fraction_lexeme", "number", "Numerical value of a simple fractional lexical expression before its whole or unit is attached.", f,
            {"half": 0.5, "quarter": 0.25}, notes="Lexical fraction candidates only; a quarter may be a coin, period or district and requires sense disambiguation.")
    for key, cue, desc in [
        ("quantity_lower_bound", "least", "Explicit inclusive lower numeric bound introduced by at least, represented without replacing it by an exact quantity."),
        ("quantity_upper_bound", "most", "Explicit inclusive upper numeric bound introduced by at most, represented without replacing it by an exact quantity."),
        ("quantity_exact_value", "exactly", "Exact numeric value explicitly constrained by exactly; the counted or measured argument remains separately bound."),
        ("quantity_approximate_value", "about", "Central numeric estimate explicitly modified by about, with unspecified tolerance retained as unknown."),
    ]:
        tests = [tok(token="at"), tok(token=cue)] if cue in {"least", "most"} else [tok(token=cue)]
        prefix = [{"token": "at"}, {"token": cue}] if cue in {"least", "most"} else [{"token": cue}]
        _native(c, key, "number", desc, f, 3,
                seq(gap(), *tests, tok("n", cardinal_value=present())), ref("n.cardinal_value"),
                [*prefix, {"token": "three", "cardinal_value": 3}],
                [{"token": "possibly"}, {"token": "three", "cardinal_value": 3}],
                mechanism="quantifier_bound_copy", scope="quantity expression")
    rows = [
        ("quantity_interval", "object", "A bounded numeric interval with explicit endpoint inclusion and counted domain, avoiding an unjustified exact point estimate.", {"lower": 2, "upper": 4, "lower_inclusive": True, "upper_inclusive": True, "domain": "apples"}, "at least two and at most four apples", "two apples and four pears", "Bind paired bounds of one quantity and derive each endpoint's inclusion from its explicit operator; keep a single counted domain.", "{lower:a.value,upper:b.value,lower_inclusive:a.operator.inclusive,upper_inclusive:b.operator.inclusive,domain:counted.domain}", "numeric_range_composition"),
        ("quantity_ratio", "object", "Ordered ratio of two specified quantities with domain labels; numerator and denominator are not interchangeable.", {"numerator": {"value": 2, "domain": "red_beads"}, "denominator": {"value": 3, "domain": "blue_beads"}}, "two red beads for every three blue beads", "two red beads and three blue beads", "Recognize explicit ratio/per construction and bind both domains.", "{numerator:{value:a.value,domain:a.domain},denominator:{value:b.value,domain:b.domain}}", "ratio_composition"),
        ("quantity_percentage", "number", "Explicit percentage value on a zero-to-one scale, independent of the referenced total.", 0.25, "twenty five percent of the beads", "twenty five beads", "Parse the numeral followed by percent, then divide by one hundred without assuming a denominator count.", "numeral.value / 100", "percentage_normalization"),
        ("normalized_measure", "object", "Magnitude converted to an agreed canonical unit while preserving original value, unit and conversion provenance.", {"value": 0.02, "unit": "m", "dimension": "length", "original": {"value": 2, "unit": "cm"}, "conversion": {"factor": 0.01, "table": "si_length_v1"}}, "two centimeters", "some centimeters", "Bind an explicit numeric magnitude and compatible unit, then use a declared dimension-specific conversion table. An unspecified magnitude cannot produce a numeric normalized value.", "{value:n.value*unit.factor,unit:unit.canonical,dimension:unit.dimension,original:{value:n.value,unit:unit.source},conversion:{factor:unit.factor,table:unit.table_id}}", "dimension_checked_unit_conversion"),
        ("measure_entity_id", "entity_ref", "Entity whose quantity or dimension the current measure describes, resolved from syntax and semantic attachment.", "e1", "the rope is two meters long", "two meters", "Attach a length measure to an explicitly available measured entity; a standalone magnitude supplies no entity ID.", "measured_entity.id", "measure_attachment"),
        ("counted_domain", "object", "Restriction defining which objects are counted, including explicit exclusions and contextual location.", {"kind": "apple", "color": "red"}, "three red apples", "A red box . three", "Compose the count noun's restrictive modifiers; an unresolved numeral after an unrelated object does not establish a counted domain.", "nominal.restriction", "count_domain_composition"),
        ("count_excluded_ids", "array", "Explicit exceptions removed from a count or quantified domain, rather than absent or unmentioned items.", ["e2"], "all children except Ben", "all children including Ben", "Bind the exception phrase to its domain and resolve excluded referents.", "exception.ids", "exception_set_binding"),
        ("quantity_total", "object", "Explicit or arithmetically justified total for one aligned domain, with units and source operands retained.", {"value": 5, "domain": "apples", "unit": "count", "operands": [2, 3]}, "two apples plus three apples", "two apples plus three pears", "Sum compatible disjoint quantities only after domain and unit alignment.", "{value:sum(aligned_disjoint_quantities),domain:aligned.domain,unit:aligned.unit,operands:source_values}", "quantity_addition"),
        ("quantity_part", "object", "Selected portion and its referenced whole, distinct from an independent count of another group.", {"part": 2, "whole": 5, "domain": "apples"}, "two of the five apples", "two apples near five pears", "Bind partitive construction to the same whole set and preserve both counts.", "{part:part.value,whole:whole.value,domain:whole.domain}", "partitive_composition"),
        ("quantity_remaining", "object", "Remaining amount after a supported removal from an explicit initial quantity, with owner and event anchors and no negative-count extrapolation.", {"value": 2, "domain": "apples", "owner_id": "e1", "after_event_id": "ev1", "scope_id": "s1"}, "Lily had five apples and gave away three", "Lily wanted five apples and gave away three", "Require asserted initial amount and a compatible asserted removal event from the same owner's inventory.", "{value:initial.value-removed.value,domain:initial.domain,owner_id:initial.owner_id,after_event_id:removal.event_id,scope_id:removal.scope_id}", "quantity_state_update"),
        ("quantity_change", "object", "Signed amount explicitly added or removed by an asserted scoped event, with inventory owner and provenance distinguished from the resulting total.", {"delta": -3, "domain": "apples", "owner_id": "e1", "event_id": "ev1", "scope_id": "s1", "factuality": "asserted"}, "Lily gave away three of her apples", "Lily imagined giving away three of her apples", "Bind transfer direction, inventory owner, domain and asserted factuality before creating an actual-inventory change candidate; imagined transfers remain in their separate world.", "{delta:signed_event_quantity,domain:quantity.domain,owner_id:inventory.owner_id,event_id:event.id,scope_id:event.scope_id,factuality:event.factuality}", "quantity_event_binding"),
        ("quantity_balance", "object", "Conservation relation between compatible before/add/remove/after amounts, retained as a check rather than invented state.", {"before": 5, "removed": 3, "after": 2, "domain": "apples", "unit": "count"}, "five apples minus three leaves two", "five apples minus three leaves four", "Verify the explicitly supplied arithmetic relation in one aligned domain.", "verified_balance_record_with_domain_and_unit", "quantity_conservation_check"),
        ("explicit_zero_count", "object", "Explicitly stated zero quantity in a restricted domain; missing observations alone never establish zero.", {"value": 0, "domain": {"kind": "apple", "container_id": "e1"}, "scope_id": "s1", "assertion_status": "asserted"}, "there are no apples in the basket", "there may be apples in the basket", "Resolve no as a scoped zero-count assertion, retaining the basket's entity identity, counted kind and assertion scope.", "{value:0,domain:restriction,scope_id:claim.scope_id,assertion_status:claim.assertion_status}", "zero_quantification_scope"),
        ("numeric_precision", "object", "Stated rounding or significant-figure precision of a numerical expression, not epistemic confidence in the underlying claim.", {"decimal_places": 1}, "rounded to one decimal place", "possibly one meter", "Bind an explicit rounding instruction to its numeric target.", "rounding_specification", "precision_instruction_binding"),
        ("range_endpoint_inclusion", "object", "Whether each endpoint belongs to a stated numeric range, based on explicit wording or declared convention.", {"lower": True, "upper": False}, "at least two but fewer than five", "some amount between two and five", "Compose explicit lower/upper comparison operators; an ambiguous between range without a declared endpoint convention cannot fix both flags.", "{lower:lower_op.inclusive,upper:upper_op.inclusive}", "bound_operator_composition"),
        ("measure_uncertainty", "object", "Explicit uncertainty radius or interval attached to a measure, preserving its base magnitude, dimension and stated interpretation.", {"base": 10, "plus_minus": 1, "unit": "cm", "dimension": "length"}, "ten centimeters plus or minus one", "ten centimeters and one second", "Bind plus-or-minus amount to a compatible base measure.", "{base:base.value,plus_minus:error.value,unit:base.unit,dimension:base.dimension}", "measurement_uncertainty_parse"),
        ("distributed_share", "object", "Per-recipient amount implied by an explicitly equal division of a known total among a known positive recipient count.", {"value": 2, "unit": "apple"}, "six apples divided equally among three children", "six apples divided unequally among three children", "Require equal distribution, compatible count units and positive recipient count before division.", "total / recipient_count", "equal_partition_arithmetic"),
        ("rate_measure", "object", "Ratio of a measure to a time or other denominator unit, with both dimensions preserved.", {"value": 2, "numerator": "m", "denominator": "s"}, "two meters per second", "two meters and a second", "Compose an explicit per construction into a dimensional rate.", "{value:n.value,numerator:u1,denominator:u2}", "rate_composition"),
        ("unit_conversion_factor", "number", "Declared factor between a source and target unit of the same dimension, never inferred between incompatible dimensions.", 100, "convert meters to centimeters", "convert meters to kilograms", "Match both units in a trusted dimensional conversion table.", "conversion[source_unit,target_unit]", "unit_conversion_lookup"),
        ("quantity_comparison", "object", "Grounded comparison of two compatible measures or counts, preserving their owners, domain and relation.", {"left": "e1", "relation": "greater", "right": "e2", "domain": "apples", "unit": "count", "left_value": 5, "right_value": 3}, "Lily has five apples and Ben has three apples", "Lily has five apples and Ben has three pears", "Align domain and counting conditions before comparing quantities.", "{left:a.owner,relation:compare(a,b),right:b.owner,domain:aligned.domain,unit:aligned.unit,left_value:a.value,right_value:b.value}", "dimension_checked_comparison"),
    ]
    for row in rows:
        _design(c, f, *row, mechanism="typed_quantity_composition")


def _provenance(c):
    f = "semantic_evidence"
    carried = [
        ("supporting_mention_indices", "array", "Positions of visible mentions supporting this event-level interpretation, preserved when the same scoped event is mentioned again.", [0]),
        ("supporting_event_ids", "array", "Identified events offered as support for the current event claim; these are support links rather than asserted causes.", ["ev1"]),
        ("supporting_proposition_ids", "array", "Identified propositions used as premises for an event claim, allowing later review of its evidential basis.", ["p1", "p2"]),
        ("source_scope_id", "string", "Scope in which a supporting claim was originally made, retained separately from the current query's scope.", "s_report"),
        ("source_claim_id", "string", "Identity of the supporting claim whose content was carried into the current interpretation.", "p1"),
        ("provenance_chain", "array", "Ordered trace of sources and transformations supporting a claim, preventing a repeated report from appearing to be independent evidence.", ["src1", "report2"]),
        ("inference_rule_id", "string", "Identity and version of the rule that produced the current claim hypothesis; the name is not a correctness guarantee.", "rule_transfer_v1"),
        ("inference_premise_ids", "array", "Explicit premise IDs used by a derivation, preserving what would need to be retracted if one premise fails.", ["p1", "p2"]),
        ("evidence_time_id", "string", "Time associated with the supporting observation, distinct from the time at which the claim is repeated.", "t1"),
        ("evidence_assumption_ids", "array", "Assumptions on which a derived event interpretation depends; they must remain visible when the claim is reused.", ["assumption1"]),
        ("evidence_assertor_id", "entity_ref", "Person explicitly responsible for asserting the current event claim, distinct from its event actor.", "e2"),
        ("evidence_anchor_bundle", "object", "Correlated claim, event, entity, source and scope anchors carried together so independent field winners cannot mix different claims.", {"claim_id": "p1", "event_id": "ev1", "entity_id": "e1", "source_id": "src1", "scope_id": "s1"}),
    ]
    for key, typ, desc, val in carried:
        _carry(c, key, typ, desc, f, val, identity="event_id", scope="claim provenance", sources=(*LOCAL, "sae.absorption"), claim_aligned=True)
    _lookup(c, "evidence_source_kind", "string", "Linguistic cue for how information was obtained, before the specific source and claim are bound.", f,
            {"reportedly": "report", "visibly": "visual_observation", "apparently": "appearance_or_inference"}, scope="source cue")
    _lookup(c, "evidence_observation_channel", "string", "Perceptual modality of an explicitly selected observation verb sense; it does not entail that the perceived proposition is true.", f,
            {"see.v.perceive": "vision", "hear.v.perceive": "hearing", "smell.v.perceive": "olfaction", "touch.v.perceive": "touch"}, field="lexical_sense_id")
    rows = [
        ("evidence_report_depth", "number", "Number of nested report-attribution steps between narrator and current claim, without treating repeated transmission as corroboration.", 2, "Lily said Ben reported the door open", "Lily saw the open door", "Count nested attributed report frames on the claim's support path.", "count(report_edges)", "report_graph_depth"),
        ("evidence_quote_source_id", "entity_ref", "Attributed speaker of a quoted piece of supporting evidence, keeping quoted assertion separate from narrator endorsement.", "e1", "Lily said : the gate is open", "Lily heard : the gate is open", "Resolve a quote's explicit speaker frame; the hearer alone is not the source.", "quote.speaker_id", "quote_source_resolution"),
        ("evidence_explicit", "boolean", "The relevant proposition is directly expressed by the visible text rather than supplied by a default or inference.", True, "The door is red", "The door looked festive", "Align the semantic claim to an explicit predication rather than a plausible inferred property.", True, "claim_text_alignment"),
        ("evidence_independent", "boolean", "Two supporting observations have distinct provenance roots under the available trace, rather than one merely quoting the other.", True, "Lily saw the door open . Ben independently saw it open", "Lily said Ben said the door was open", "Compare provenance roots and explicit independence evidence; unknown provenance must not count as independence.", True, "provenance_independence_check"),
        ("evidence_conflict", "object", "Supporting claims disagree about the same scoped referent/property/time, preserving both sources rather than averaging truth.", {"claims": ["p1", "p2"], "property": "open"}, "Lily says the door is open now . Ben says it is closed now", "Lily says one door is open . Ben says another is closed", "Align entity, property, time and scope before declaring source conflict.", "{claims:[p1.id,p2.id],property:aligned_property}", "claim_alignment_conflict"),
        ("evidence_retracted", "object", "A source explicitly withdraws a previous claim; this weakens that claim's support without asserting its logical opposite.", {"claim": "p1", "by": "e1"}, "Lily said the door was open . Lily withdrew that claim", "Lily said the door was open . Ben disagreed", "Bind an explicit retraction to the retracting source's earlier claim.", "{claim:prior.id,by:source.id}", "retraction_resolution"),
        ("evidence_supersedes", "object", "An explicit correction identifies a prior claim and its replacement, without changing the earlier causal record.", {"old": "p1", "new": "p2"}, "Lily said blue . She corrected it to green", "Lily said blue . Ben said green", "Bind self-correction and replacement to the same claim slot; mere disagreement is not supersession.", "{old:old_claim.id,new:new_claim.id}", "claim_correction_linking"),
        ("evidence_missing", "object", "A required premise for a particular inference is unavailable; this describes proof status rather than falsity of the conclusion.", {"needed": "owner_before_transfer"}, "Lily gave away a key . Its earlier owner is unknown", "Lily owned the key . Lily gave it away", "Inspect the selected inference's declared premises and mark a missing owner fact without inventing one.", "missing_required_premise", "premise_availability_test"),
        ("evidence_freshness", "object", "Temporal applicability of an observation relative to the current query, distinguishing old evidence from currently confirmed evidence.", {"status": "possibly_stale", "source_time": "t1"}, "Yesterday the door was open . Today", "The door is open right now", "Compare evidence time to query time and intervening change opportunities; do not declare persistence without support.", "freshness_assessment", "evidence_temporal_applicability"),
        ("evidence_access_holder", "entity_ref", "Character for whom a particular observation is accessible, without making that observation common knowledge.", "e1", "Only Lily saw the key fall", "Lily and Ben both saw the key fall", "Bind explicit exclusive perceptual access to the observation and its observer.", "exclusive_observer.id", "epistemic_access_binding"),
        ("evidence_counterexample", "object", "A grounded instance that violates a particular proposed generalization within its stated domain.", {"rule": "r1", "instance": "e1"}, "All cups are red . This cup is blue and not red", "All cups are red . This plate is blue and not red", "Match the universal's domain and verify the instance's explicitly negated predicate in the same scope; distinct color names alone do not exclude a multicolored object.", "{rule:rule.id,instance:instance.id}", "counterexample_matching"),
        ("evidence_coverage_domain", "object", "The set of cases over which evidence is explicitly claimed to be exhaustive; uninspected cases remain outside the claim.", {"domain": "basket", "exhaustive": True}, "Lily checked every apple in the basket", "Lily checked some apples in the basket", "Bind explicit exhaustive inspection to the restricted domain, not the world at large.", "{domain:inspection.domain,exhaustive:true}", "evidence_domain_coverage"),
        ("evidence_exception_ids", "array", "Grounded exceptions to a stated rule, preserving that exceptions narrow applicability rather than invalidate unrelated instances.", ["e2"], "Every child except Ben has a ticket", "Every child including Ben has a ticket", "Bind explicit exception identities to the quantified rule's domain.", "exception.ids", "rule_exception_binding"),
        ("evidence_rule_scope", "object", "Conditions and context limiting a stated rule's validity, including quoted, imagined or local-world rules.", {"world": "game1", "condition": "inside_game"}, "In this game all birds swim", "All birds swim everywhere", "Attach the explicitly restricted game-world scope to the rule; do not export it as narrator-world knowledge.", "rule.scoped_domain", "rule_scope_binding"),
        ("evidence_defeasible", "boolean", "The current support licenses a default or typical conclusion that may be overridden by a more specific stated exception.", True, "Birds usually fly", "All birds in this room are flying", "Recognize typical/default force and retain exception sensitivity.", True, "default_force_analysis"),
        ("evidence_candidate_only", "boolean", "A semantic bundle is being proposed for an interpretation or next-token alternative and has not been accepted as observed context.", True, "Suppose Lily took the key", "Lily took the key", "Bind the explicit supposition/operator or generation-candidate boundary; candidate status must remain scoped.", True, "candidate_scope_tracking"),
        ("evidence_world_status", "string", "Whether a claim belongs to actual narration, a quoted report, a hypothetical branch or a fictional substory, without collapsing these contexts.", "hypothetical", "If Lily opened the door", "Lily opened the door", "Resolve enclosing semantic worlds and assertion operators for the current proposition.", "innermost_world.status", "semantic_world_stack"),
        ("evidence_resolution_status", "string", "Whether an interpretation's required entity/event/scope links are complete, ambiguous or unresolved, independent of its probability.", "ambiguous", "Lily met Mira . She left", "Lily was alone . She left", "Inspect all required binding alternatives and mark ambiguity when more than one remains supported.", "binding_completeness_status", "semantic_binding_audit"),
    ]
    for row in rows:
        _design(c, f, *row, mechanism="provenance_reasoning", sources=(*LOCAL, "sae.absorption", "circuits.tracing"))


def _lexical(c):
    f = "lexical_semantics"
    rows = [
        ("lexical_sense_candidates", "array", "Plausible lexical senses for an ambiguous expression before contextual disambiguation; none is silently treated as the sole sense.", {"bank": ["bank:river_edge", "bank:financial"]}, "lemma"),
        ("lexical_hypernyms", "array", "Immediate broader type concepts of the selected sense, used as lexical evidence rather than story-specific membership facts.", {"rabbit:animal": ["animal"], "scissors:tool": ["cutting_tool"]}, "lexical_sense_id"),
        ("lexical_hyponyms", "array", "Illustrative narrower lexical kinds under a selected kind sense; the list does not assert instances or exhaustive coverage.", {"animal:organism": ["rabbit", "dog"], "tool:implement": ["scissors", "hammer"]}, "lexical_sense_id"),
        ("lexical_synonyms", "array", "Context-compatible alternative lexicalizations of one selected sense, not interchangeable surface words in every construction.", {"begin:start": ["start", "commence"], "small:size": ["little"]}, "lexical_sense_id"),
        ("lexical_antonyms", "array", "Lexical opposites of a selected sense; antonymy does not mean every proposition containing one logically negates the other.", {"hot:temperature": ["cold"], "open:aperture": ["closed"]}, "lexical_sense_id"),
        ("lexical_part_types", "array", "Conventional part kinds associated with a selected whole kind, without asserting that a particular instance has all parts.", {"bicycle:vehicle": ["wheel", "pedal"], "tree:plant": ["root", "branch"]}, "lexical_sense_id"),
        ("lexical_whole_types", "array", "Conventional whole kinds associated with a selected part sense; actual part ownership still requires discourse evidence.", {"petal:flower_part": ["flower"], "pedal:bicycle_part": ["bicycle"]}, "lexical_sense_id"),
        ("lexical_member_types", "array", "Kinds of members associated with a group-kind sense, distinguished from actual group member IDs.", {"flock:bird_group": ["bird"], "forest:tree_group": ["tree"]}, "lexical_sense_id"),
        ("lexical_substance_types", "array", "Conventional material constituents of a selected substance/composite sense, not a measured physical composition.", {"ice:frozen_water": ["water"], "wood:tree_material": ["plant_material"]}, "lexical_sense_id"),
        ("lexical_entailment_templates", "array", "Event-type entailment candidates associated with a sense, requiring aligned participants, modality and assertion scope before use.", {"snore:sleep_sound": ["sleep"], "buy:purchase": ["obtain_ownership"]}, "lexical_sense_id"),
        ("lexical_causative_partner", "string", "Noncausative change predicate related to a causative lexical sense, without inferring an actual event from the type relation.", {"kill:cause_death": "die", "raise:move_up": "rise"}, "lexical_sense_id"),
        ("lexical_manner_supertype", "string", "Broader event type modified by the selected manner-of-action verb sense.", {"whisper:speak_softly": "speak", "sprint:run_fast": "run"}, "lexical_sense_id"),
        ("lexical_derivational_family", "array", "Related lexical forms sharing a derivational base while retaining their distinct parts of speech and argument structures.", {"repair:restore": ["repair", "repairer", "repairable"], "decide:choose": ["decide", "decision"]}, "lexical_sense_id"),
        ("lexical_topic_domain", "string", "Subject-matter domain of the selected lexical sense, useful for interpretation without assigning a topic to the entire story.", {"rook:chess_piece": "chess", "denominator:fraction": "arithmetic"}, "lexical_sense_id"),
        ("lexical_usage_register", "string", "Register associated with the selected expression, independent of the speaker's identity or social status.", {"commence:start_formal": "formal", "kid:child_informal": "informal"}, "lexical_sense_id"),
        ("lexical_regional_variant", "object", "Language-variety association for an expression and equivalent sense, without inferring the author's nationality.", {"lift:elevator_uk": {"variety": "British_English", "equivalent": "elevator"}}, "lexical_sense_id"),
        ("lexical_gloss", "string", "Short human-readable definition of the selected sense for inspection, not a hidden executable semantic program.", {"scissors:tool": "A cutting tool with two joined blades.", "bank:river_edge": "Land along the side of a river."}, "lexical_sense_id"),
        ("lexical_supersense", "string", "Coarse lexical-semantic class of a selected sense, used alongside rather than in place of its more specific meaning.", {"rabbit:animal": "noun.animal", "scissors:tool": "noun.artifact"}, "lexical_sense_id"),
        ("lexical_selection_preferences", "object", "Soft semantic preferences of a predicate sense for its roles, not hard bans on figurative or fictional uses.", {"drink:ingest_liquid": {"patient": "liquid", "constraint": "soft"}}, "lexical_sense_id"),
        ("lexical_scale_dimension", "string", "Dimension conventionally graded by an adjective sense, distinct from any measured value of a particular entity.", {"hot:temperature": "temperature", "long:length": "length", "heavy:mass": "mass"}, "lexical_sense_id"),
        ("lexical_scale_direction", "string", "Direction on the associated comparison scale expressed by the selected adjective sense.", {"hot:temperature": "higher", "cold:temperature": "lower", "heavy:mass": "higher"}, "lexical_sense_id"),
        ("lexical_animacy_expectation", "string", "Lexical expectation about a referent kind's animacy, defeasible under personification or story-specific evidence.", {"rabbit:animal": "animate", "stone:rock": "inanimate"}, "lexical_sense_id"),
        ("lexical_countability", "string", "Count/mass construal associated with a noun sense; contextual coercion can supply a different interpretation.", {"water:substance": "mass", "apple:fruit_individual": "count"}, "lexical_sense_id"),
        ("lexical_collectivity", "boolean", "The selected noun sense denotes a collective group rather than one ordinary member, without choosing grammatical agreement.", {"flock:bird_group": True, "bird:individual": False}, "lexical_sense_id"),
        ("lexical_relation_arity", "number", "Number of semantic arguments intrinsic to a relational noun or predicate sense, distinct from optional adjuncts.", {"sibling:kin_relation": 2, "between:spatial_relation": 3}, "lexical_sense_id"),
        ("lexical_eventuality_class", "string", "Default aspectual class of a selected predicate sense before argument and modifier composition.", {"know:state": "state", "run:activity": "activity", "arrive:achievement": "achievement"}, "lexical_sense_id"),
        ("lexical_agentivity", "string", "Whether a selected event sense conventionally permits intentional control; individual event intentionality remains separate.", {"sneeze:bodily_event": "normally_nonvolitional", "promise:commitment": "normally_volitional"}, "lexical_sense_id"),
        ("lexical_telicity", "string", "Lexical endpoint tendency of a predicate sense before object quantization and contextual coercion are applied.", {"arrive:achievement": "bounded", "wander:activity": "unbounded"}, "lexical_sense_id"),
        ("lexical_modifier_mode", "string", "How an adjective sense composes with its noun: intersective, subsective or privative, rather than flat attribute conjunction.", {"red:color": "intersective", "skillful:ability": "subsective", "fake:imitation": "privative"}, "lexical_sense_id"),
        ("lexical_factivity", "string", "Conventional complement presupposition behavior of a selected predicate sense, subject to embedding and projection constraints.", {"regret:attitude": "factive", "believe:attitude": "nonfactive"}, "lexical_sense_id"),
        ("lexical_implicativity", "object", "Conventional polarity-conditioned complement signature of a selected predicate construction; using it for inference requires resolved assertion, negation, modal and aspectual scope.", {"manage:successful_attempt": {"construction": "manage_to_infinitive", "positive": "complement_holds", "negative": "complement_does_not_hold", "guard": "ordinary_episodic_assertion_not_metalinguistic_negation"}}, "lexical_sense_id"),
        ("lexical_idiom_reading", "object", "Conventional non-compositional meaning candidate of a recognized expression, alongside any surviving literal reading.", {"kick_the_bucket:idiom": {"meaning": "die", "reading": "idiomatic"}}, "lexical_sense_id"),
    ]
    for key, typ, desc, mapping, field in rows:
        _lookup(c, key, typ, desc, f, mapping, field=field, sources=(("lexical.implicatives", "local.storyformer") if key == "lexical_implicativity" else ("wordnet", "local.storyformer")),
                scope="selected lexical sense",
                notes="Relation categories are motivated by lexical semantics. KV values and colon-delimited sense labels are authored examples, not a claimed export of WordNet. An upstream causal sense analysis is required; this table neither commits world facts nor resolves lexical ambiguity.")


def _retrieval(c):
    f = "contextual_retrieval"
    alignments = [
        ("retrieval_lexeme_recurrence", "lemma", "rabbit", "A pair of visible mentions sharing a lexical base, retaining source positions rather than treating them as one entity."),
        ("retrieval_entity_recurrence", "entity_id", "e1", "A pair of mentions already resolved to the same entity, useful as a retrieval route without re-solving identity."),
        ("retrieval_event_recurrence", "event_id", "ev1", "Two mentions attached to the same identified event, preserving a route for copying its already known attributes."),
        ("retrieval_actor_alignment", "actor_id", "e1", "Two event mentions with the same resolved actor, without assuming that the events themselves are identical."),
        ("retrieval_recipient_alignment", "recipient_id", "e2", "Two event mentions with the same recipient identity, useful for comparing transfers without merging them."),
        ("retrieval_sense_alignment", "lexical_sense_id", "bank:river_edge", "Two occurrences sharing a selected lexical sense, distinguished from spelling-only repetition."),
        ("retrieval_role_parallelism", "role", "patient", "Two already interpreted mentions occupying the same semantic role, preserving their separate identities."),
        ("retrieval_event_kind_alignment", "event_type", "repair", "Two event mentions of the same coarse type, a possible analogy key rather than evidence of one event."),
        ("retrieval_assertion_alignment", "factuality", "reported", "Two mentions with the same annotation factuality status, useful for keeping reported evidence separate from asserted evidence."),
        ("retrieval_source_alignment", "evidence_source_id", "src1", "Two claims sharing a provenance source, useful for detecting repeated rather than independent evidence."),
        ("retrieval_kind_alignment", "entity", "rabbit", "Two mentions with the same coarse entity label, without equating their entity identifiers."),
        ("retrieval_name_collision", "entity_name", "Lily", "Repeated use of the same name at distinct positions; this is a collision alert, not proof of shared identity."),
    ]
    for key, field, val, desc in alignments:
        expected = {"source_index": 0, "query_index": 2, "matched_value": val}
        first = {"token": "source", "index": 0, field: val, "scope_id": "s1"}
        query = {"token": "query", "index": 2, field: val, "scope_id": "s1"}
        _native(c, key, "object", desc, f, expected,
                seq(gap(), tok("source", **{field: present(), "index": present(), "scope_id": present()}), gap(),
                    tok("target", **{field: ref(f"source.{field}"), "index": present(), "scope_id": ref("source.scope_id")})),
                {"source_index": ref("source.index"), "query_index": ref("target.index"), "matched_value": ref(f"source.{field}")},
                [first, {"token": "then"}, query], [first, {"token": "then"}, {**query, "scope_id": "s2"}],
                mechanism="equality_key_retrieval", scope="pair of visible mentions", sources=("circuits.induction", "circuits.binding", "local.storyformer"),
                notes="Every compatible earlier binding may activate. This proposes an alignment record, not nearest-match selection, identity merging or current-world persistence.")
    rows = [
        ("retrieval_continuation_candidates", "array", "Earlier observed successors of a matching suffix, collected as possible continuations without reading after the current query.", ["bell"], "brass bell rang . brass", "brass", "Match an earlier occurrence of the current suffix and collect only successors already inside the visible prefix.", "observed_successors(matched_suffix)", "causal_suffix_index"),
        ("retrieval_long_prefix_match", "object", "Earlier matching multiword prefix with its known successor and source span, distinguishing longer-context induction from a one-word match.", {"prefix": ["small", "brass"], "next": "bell"}, "small brass bell . small brass", "small brass bell . large brass", "Align the full current suffix with an earlier contiguous span and copy the already observed successor.", "{prefix:suffix,next:earlier_successor}", "multiword_suffix_matching"),
        ("retrieval_definition_binding", "object", "A local explicitly stated definition retrieved for a later use of its term, overriding generic associations only within that definition's scope.", {"term": "dax", "meaning": "blue key"}, "Here dax means blue key . Find the dax", "Here dax sounds like blue . Find the key", "Index an explicit definition and retrieve its content on later term use within the same scope.", "local_definition_binding", "definition_index"),
        ("retrieval_property_answer", "object", "Value of a requested property retrieved for a specified entity and applicable time, preserving the source assertion.", {"entity": "e1", "property": "color", "value": "red"}, "The cup is red . The cup color is", "The cup may be red . Its known color is", "Match query entity and property to an applicable asserted relation; abstain if the requested knowledge status exceeds the evidence.", "matched_property_bundle", "scoped_property_retrieval"),
        ("retrieval_relation_answer", "object", "A relation target retrieved using both the relation kind and source entity, rather than global name salience.", {"source": "e1", "relation": "owner", "target": "e2"}, "Ben owns the cup . The cup owner is", "Ben sees the cup . The cup owner is", "Bind the requested owner relation to a possession fact about the cup.", "matched_relation_bundle", "relation_key_retrieval"),
        ("retrieval_role_exclusion", "array", "Entities explicitly incompatible with a requested event role, used to suppress only those candidates under the current role query.", ["e1"], "Lily gave the key to someone else . The recipient was", "Lily kept the key . Its holder was", "Use explicit someone-else distinction to exclude the actor from recipient candidates, without a universal self-transfer ban.", "role_forbidden_ids", "role_constraint_filter"),
        ("retrieval_comparison_set", "array", "Entities explicitly placed in one comparison domain, avoiding unrelated salient mentions as comparison competitors.", ["e1", "e2"], "Of Lily and Ben who is taller", "Lily met Ben . A tree is taller", "Resolve the of-set as the comparison domain and preserve members separately.", "comparison_domain.ids", "comparison_domain_resolution"),
        ("retrieval_parallel_slot", "object", "Corresponding role or position across explicitly parallel structures, without treating superficial word order as guaranteed semantic alignment.", {"left_slot": "object", "right_slot": "object"}, "Lily took a cup and Ben took a bowl", "Lily took a cup while Ben slept", "Align two matching predicate frames and their filled object slots.", "aligned_frame_slots", "structural_parallel_alignment"),
        ("retrieval_list_members", "array", "Semantic items belonging to a completed visible list, excluding conjunctions, separators and unrelated following text.", ["scissors", "needle", "thread"], "tools : scissors , needle and thread", "scissors fell . Needle is a name", "Parse one coordinated enumeration and collect its member denotations.", "list.member_denotations", "enumeration_parse"),
        ("retrieval_list_correspondence", "object", "Same-rank items in explicitly aligned lists, retaining the list identities and rank used for the correspondence.", {"rank": 2, "left": "Ben", "right": "blue"}, "Lily Ben ; red blue ; colors respectively", "Lily Ben ; red blue ; colors randomly", "Require an explicit alignment instruction such as respectively before pairing list ranks.", "rank_aligned_pairs", "parallel_list_indexing"),
        ("retrieval_ordered_successor", "string", "Next element in a specified ordered series, using a declared sequence rather than arbitrary lexical association.", "Wednesday", "Tuesday ; the next day is", "Tuesday ; the previous day is", "Bind a successor request to a declared weekday order and current item.", "successor(weekday_order,current)", "ordered_series_lookup"),
        ("retrieval_set_membership", "object", "Evidence that a named entity is in an explicitly stated finite set, without applying open-world defaults.", {"member": "e1", "set": "team1"}, "Team one includes Lily . Lily belongs to", "Team one may include Lily . Lily definitely belongs to", "Match an asserted member-set relation with compatible scope and requested certainty.", "membership_bundle", "explicit_set_retrieval"),
        ("retrieval_default_override", "object", "A specific stated exception defeats an applicable general default for one entity, preserving the default for other entities.", {"default": "birds_fly", "exception": "this_bird_cannot"}, "Birds usually fly . This bird cannot fly", "Birds usually fly . This bird is blue", "Align exception subject/property with default domain and detect explicit incompatibility.", "default_exception_pair", "specificity_and_default_reasoning"),
        ("retrieval_correction_target", "string", "Earlier claim specifically referred to by an explicit correction, allowing suppression of its support without deleting its trace.", "p1", "The cup is red . Correction : it is blue", "The cup is red . Another cup is blue", "Resolve correction and pronoun to the same claim slot and entity.", "corrected_claim.id", "correction_reference_resolution"),
        ("retrieval_contradiction_pair", "object", "Two retrieved claims about one aligned proposition disagree under compatible time and scope, preserving both for review.", {"claims": ["p1", "p2"]}, "The door is open now . The same door is closed now", "The door was open yesterday . It is closed now", "Align referent, property, time and world before marking a contradiction candidate.", "aligned_conflicting_claims", "proposition_alignment"),
        ("retrieval_missing_role", "object", "A role remains unfilled in a recognized frame at this prefix, supplying a continuation constraint without inventing its filler.", {"event": "ev1", "role": "destination"}, "Lily put the cup", "Lily put the cup on the table", "Consult active put-frame slots and mark its destination as unresolved until a licensed location complement arrives.", "unfilled_frame_role", "incremental_frame_completion"),
        ("retrieval_two_hop_relation", "object", "A composed relation obtained through two compatible explicit relation edges, with the intermediate entity preserved.", {"path": ["e1", "e2", "e3"], "relation": "inside_transitive"}, "The key is in the box . The box is in the bag", "The key is near the box . The box is in the bag", "Compose only declared transitive containment edges in one world/time, not arbitrary relation chains.", "typed_two_edge_path", "relation_graph_join"),
        ("retrieval_inverse_relation", "object", "Inverse view of an explicit relation, with a declared inverse rule and unchanged scope/provenance.", {"source": "e2", "relation": "owned_by", "target": "e1"}, "Lily owns the cup", "Lily wants the cup", "Apply declared owns/owned_by inversion only to an ownership assertion.", "invert(explicit_ownership)", "typed_relation_inverse"),
        ("retrieval_analogy_mapping", "object", "Role-preserving correspondence between two described situations, offered as an analogy hypothesis rather than transferred facts.", {"source_role": "instrument", "target_role": "instrument"}, "Scissors cut paper as shears cut cloth", "Scissors cut paper while shears lie nearby", "Align predicates and participant roles across an explicit analogy construction.", "role_preserving_mapping", "relational_analogy_alignment"),
        ("retrieval_evidence_union", "object", "Compatible evidence from distinct prefix sources combined for the same claim while preserving each support path and dependence relation.", {"claim": "p1", "sources": ["src1", "src2"]}, "Lily and Ben independently saw the door open", "Lily repeated Ben saying the door was open", "Align claim identity and retain distinct verified provenance roots; do not count copied reports twice.", "dependency_aware_evidence_union", "provenance_graph_union"),
    ]
    for row in rows:
        _design(c, f, *row, sources=("local.head_catalog", "circuits.induction", "circuits.binding"), mechanism="semantic_key_value_retrieval")


def _logical(c):
    f = "logical_semantics"
    rows = [
        ("proposition_id", "string", "Identifier for a structured predication including its participants and scope, independent of its surface wording and truth status.", "p1", "Lily opened the door", "the open door", "Recognize a completed predication and allocate a proposition identity; an attributive phrase alone is not this clause-level assertion.", "predication.id", "proposition_construction"),
        ("proposition_content", "object", "Correlated predicate and argument structure of a proposition, excluding assertion commitment so quoted and hypothetical contents can be shared.", {"predicate": "open", "actor": "e1", "patient": "e2"}, "Lily opened the door", "Lily mentioned opening", "Compose a resolved predicate frame and its filled semantic arguments.", "predicate_argument_bundle", "semantic_composition"),
        ("proposition_polarity", "string", "Positive or negative predication within an explicitly resolved scope; lexical antonymy alone is not logical negation.", "negative", "Lily did not open the door", "Lily opened a closed door", "Attach not to the relevant predication rather than to a nearby descriptive adjective.", "negative", "negation_scope_resolution"),
        ("negation_scope_id", "string", "Identity of the semantic content governed by a negation operator, distinguishing clause, constituent and metalinguistic negation.", "p1", "Lily did not say the door opened", "Lily said the door did not open", "Resolve not over the matrix saying event in the positive example; embedded negation has a different target.", "negated_content.id", "operator_scope_parse"),
        ("scope_operator", "string", "Semantic operator introduced at this prefix, awaiting or governing a scoped proposition rather than asserting that proposition.", "conditional", "if Lily opens the door", "Lily opens the door", "Recognize if as conditional operator with an antecedent clause.", "conditional", "scope_operator_binding"),
        ("quantifier_binding", "object", "A quantified variable, its restriction and its nuclear scope kept together, avoiding a flat bag of noun attributes.", {"variable": "x", "quantifier": "every", "restriction": "child"}, "Every child smiled", "A child named Every smiled", "Resolve determiner every as a quantifier binding the nominal variable and predicate scope.", "quantifier_variable_bundle", "quantifier_scope_construction"),
        ("quantifier_domain_restriction", "object", "Contextual restriction limiting a quantifier's domain, separate from the quantifier's logical force.", {"kind": "child", "location": "garden"}, "Every child in the garden smiled", "Every child smiled in the garden", "Attach in-the-garden to the quantified nominal rather than the smiling event.", "nominal_domain_restriction", "quantifier_restriction_attachment"),
        ("existential_witness", "object", "A discourse witness introduced inside an existential scope, without exporting it through negation or hypothetical branches.", {"variable": "x", "scope": "s1", "kind": "key"}, "There is a key in the box", "There is no key in the box", "Introduce a witness only for positive existential scope; retain the scope boundary.", "scoped_existential_witness", "existential_introduction"),
        ("universal_variable", "object", "Bound variable representing arbitrary members of a restricted domain, never one ordinary named entity.", {"variable": "x", "domain": "child"}, "Every child has a hat", "A child has every hat", "Bind the universal's child variable and distinguish the object quantifier in the contrasting clause.", "universal_bound_variable", "universal_binding"),
        ("disjunction_alternatives", "array", "Alternative scoped propositions or denotations introduced by disjunction, without asserting all alternatives.", ["p1", "p2"], "Lily will sing or dance", "Lily will sing and dance", "Build alternatives under or while retaining shared modal scope and participants.", "disjunct_contents", "disjunction_composition"),
        ("conjunction_members", "array", "Contents combined conjunctively in the current construction, preserving whether they are entities, predicates or propositions.", ["p1", "p2"], "Lily sang and Ben danced", "Lily sang or Ben danced", "Compose completed clause conjuncts under and, not an alternatives operator.", "conjunct_contents", "conjunction_composition"),
        ("conditional_antecedent_id", "string", "Proposition serving as the antecedent of a conditional, with no assertion that it actually holds.", "p1", "If Lily leaves Ben waits", "Because Lily leaves Ben waits", "Bind the if-clause content as antecedent, distinguished from asserted causal premises.", "if_clause.proposition_id", "conditional_composition"),
        ("conditional_consequent_id", "string", "Proposition stated to follow within a conditional interpretation, rather than an unconditional narrator assertion.", "p2", "If Lily leaves Ben waits", "Lily leaves and Ben waits", "Bind the main consequence to the conditional operator introduced by if.", "then_clause.proposition_id", "conditional_composition"),
        ("sufficient_condition", "object", "Explicit rule making one condition sufficient for a conclusion within its stated domain, without inferring the converse.", {"if": "p1", "then": "p2"}, "If the switch closes the lamp lights", "The lamp lights only if the switch closes", "Preserve implication direction; only-if expresses the opposite necessity relation.", "directed_implication", "condition_direction_analysis"),
        ("necessary_condition", "object", "Explicit requirement that must hold for another proposition, without asserting it is sufficient.", {"requires": "p1", "for": "p2"}, "The lamp lights only if the switch closes", "If the switch closes the lamp lights", "Resolve only-if necessity and retain direction from lighting to switch closure.", "directed_necessity", "condition_direction_analysis"),
        ("biconditional_relation", "object", "Explicit two-way conditional equivalence, requiring both directions rather than guessing them from one conditional.", {"left": "p1", "right": "p2"}, "The lamp lights if and only if the switch closes", "The lamp lights if the switch closes", "Recognize the complete if-and-only-if operator over two proposition contents.", "bidirectional_implication", "biconditional_parse"),
        ("exclusive_alternatives", "object", "Alternatives explicitly constrained so that at most one may hold; ordinary or remains potentially inclusive.", {"alternatives": ["p1", "p2"], "at_most_one": True}, "Lily sings or dances but not both", "Lily sings or dances", "Require explicit exclusion of joint satisfaction rather than treating every or as exclusive.", "exclusive_disjunction_bundle", "exclusive_operator_composition"),
        ("logical_exception_rule", "object", "An exception-qualified generalization with domain, default conclusion and excluded cases kept together.", {"domain": "birds", "except": "penguins", "predicate": "fly"}, "Birds fly except penguins", "Birds fly near penguins", "Attach except to the quantified rule as an exception restriction.", "rule_with_exception_domain", "exception_rule_composition"),
        ("logical_default_condition", "object", "Condition under which a defeasible rule normally applies, with explicit default force and no closed-world inference.", {"if": "bird", "normally": "fly"}, "Birds normally fly", "All these birds are flying", "Recognize generic typicality and retain its defeasible status.", "defeasible_conditional", "default_semantics"),
        ("counterfactual_premise", "object", "Assumed antecedent in a counterfactual branch, without rewriting the actual-story state.", {"content": "p1", "world": "w_counterfactual"}, "If Lily had taken the key she would have opened the door", "If Lily takes the key she may open the door", "Resolve counterfactual morphology and bind a separate branch with its premise.", "counterfactual_branch_assumption", "counterfactual_world_construction"),
        ("counterfactual_consequence", "object", "Consequence asserted only under a counterfactual premise, distinct from an actual observed outcome.", {"content": "p2", "world": "w_counterfactual"}, "If Lily had taken the key she would have opened the door", "Lily took the key and opened the door", "Bind the would-have consequence to the established counterfactual branch.", "counterfactual_branch_consequence", "counterfactual_scope_binding"),
        ("modal_base", "object", "Set or kind of possibilities relevant to a modal interpretation, such as ability, rules or available evidence.", {"kind": "ability", "holder": "e1"}, "Lily can lift the box with her strength", "Lily may lift the box under the rules", "Resolve ability modality from context, excluding the permission reading in the near miss.", "modal_context_bundle", "modal_sense_resolution"),
        ("semantic_world_id", "string", "Identity of the actual, imagined, quoted or counterfactual world in which a proposition is evaluated.", "w_dream", "In Lily's dream the cup flew", "Lily saw the cup fly", "Open an imagined-world frame and keep its predications separate from actual narration.", "active_semantic_world.id", "semantic_world_tracking"),
        ("truth_commitment", "string", "Whether the current speaker/narrator commits to a proposition, suspends it, denies it or attributes it to another source.", "suspended", "Perhaps the key is here", "The key is here", "Resolve the epistemic operator over the current proposition; perhaps suspends categorical commitment.", "suspended", "assertion_commitment_analysis"),
        ("closed_domain_license", "object", "Explicit evidence that a domain is complete enough for a specific closed-world query; it never licenses global absence reasoning.", {"domain": "box_contents", "complete": True}, "The box contains only a key and a coin", "The box contains a key and a coin", "Require only/exhaustive enumeration for this domain before licensing complement-set conclusions.", "scoped_completeness_license", "domain_completeness_proof"),
        ("entailment_candidate", "object", "Premise-to-conclusion relation proposed by a declared inference rule with matched arguments and scope; it remains an auditable hypothesis.", {"premise": "p1", "conclusion": "p2", "rule": "conjunction_elimination"}, "Lily sang and danced . Therefore Lily sang", "Lily sang or danced . Therefore Lily sang", "Use conjunction elimination only for conjunction, preserving the actor and world.", "entailed_proposition_bundle", "typed_logical_inference"),
        ("logical_contradiction", "object", "A proposition and its scoped negation are both supported under aligned identity and time, not merely different descriptions.", {"positive": "p1", "negative": "p2"}, "The same door is open now and is not open now", "The door was open then and is not open now", "Unify proposition arguments/time/world before pairing positive and negated content.", "contradictory_proposition_pair", "proposition_unification"),
        ("semantic_equivalence", "object", "Two representations express the same content under a justified paraphrase or logical transformation, not just similar vocabulary.", {"left": "p1", "right": "p2", "basis": "active_passive"}, "Lily opened the door . The door was opened by Lily", "Lily opened the door . Lily was opened by the door", "Align active/passive semantic roles rather than matching noun order.", "equivalent_content_pair", "role_preserving_equivalence"),
        ("active_assumptions", "array", "Assumptions currently in force in a reasoning branch, removed from applicability when their scope closes.", ["p1"], "Assume the key is inside . Then", "The key might be inside . Elsewhere", "Track explicit assume/discharge boundaries and retain the branch's current assumption set.", "active_assumption_ids", "assumption_stack"),
        ("inference_obligation", "object", "A required premise or binding that must be established before a proposed inference may emit its conclusion.", {"needed": "same_entity", "rule": "property_join"}, "A cup is red . This object may be that cup", "This is the same cup . The cup is red", "Expose unresolved identity needed for property transfer; do not transfer before identity is established.", "unsatisfied_inference_premise", "proof_obligation_tracking"),
        ("presupposition_projection", "object", "A presupposed content's candidate accessibility through an embedding operator, retained separately from asserted content.", {"content": "p1", "status": "presupposed"}, "Lily regrets losing the key", "Lily imagines losing the key", "Use the selected factive sense and its complement structure; preserve source and potential contextual cancellation.", "factive_complement_presupposition", "presupposition_projection_analysis"),
        ("nonmonotonic_revision", "object", "A newly established exception withdraws a previously defeasible conclusion while preserving the original premise and provenance.", {"withdraw": "p2", "because": "p3"}, "Birds usually fly . This is a bird . It cannot fly", "Birds usually fly . This is a bird . It is small", "Match explicit exception to the default conclusion and revoke only that conclusion's defeasible support.", "defeasible_support_retraction", "truth_maintenance"),
    ]
    for row in rows:
        _design(c, f, *row, sources=("codeco", "ace", "gf.reference", "local.storyformer"), mechanism="scoped_logical_composition")


def _suppression_heads(c):
    """Some associated features *control* inhibition instead of being its output.

    Keep the descriptive attribute in the registry, but make these concrete heads
    operate on an existing hypothesis. This avoids inventing a second name for
    the same semantic value just because a different detector produced it.
    """
    by_key = {a["key"]: i for i, a in enumerate(c.attributes)}
    cases = [
        ("evidence_retracted", "truth_commitment", "endorsed", {"claim": "p1", "by": "e1"},
         {"source_claim_id": "p1"}, "evidence_retracted.claim", "query.source_claim_id",
         "Suppress endorsement of the specifically retracted claim; retraction is not proof of its opposite."),
        ("evidence_supersedes", "proposition_content", {"predicate": "red", "entity_id": "e1"}, {"old": "p1", "new": "p2"},
         {"source_claim_id": "p1"}, "evidence_supersedes.old", "query.source_claim_id",
         "Suppress the old content at a current correction query after an explicit same-source replacement is resolved."),
        ("nonmonotonic_revision", "proposition_content", {"predicate": "flies", "entity_id": "e1"}, {"withdraw": "p1", "because": "p3"},
         {"source_claim_id": "p1"}, "nonmonotonic_revision.withdraw", "query.source_claim_id",
         "Subtract support for the specifically withdrawn defeasible content while retaining its original trace."),
        ("inference_obligation", "entailment_candidate", {"premise": "p1", "conclusion": "p2", "rule": "property_join"},
         {"needed": "same_entity", "rule": "property_join"}, {}, "inference_obligation.rule", "query.entailment_candidate.rule",
         "Suppress a proposed entailment whose own inference rule has an unresolved required premise; do not negate the conclusion."),
    ]
    for key, target, old, control, extra, test_path, reference, description in cases:
        index = by_key[key]
        head, grammar = c.heads[index], c.grammars[index]
        positive = {"token": "correction", key: control, target: old, **extra}
        negative = deepcopy(positive)
        field = test_path.split(".")[-1]
        negative[key][field] = "different_claim_or_rule"
        spec = neuron(seq(gap(), tok(**{target: present(), key: present(), test_path: ref(reference)})),
                      {target: ref(f"query.{target}")})
        spec["name"] = f"suppress_using_{key}"
        reads = sorted({key, target, *extra})
        head.update(name=spec["name"], function=description, mechanism="claim_keyed_evidence_suppression",
                    operation="suppress", reads=reads, writes=[target], runtime_support="native", requires=[])
        grammar.update(name=spec["name"], intent=description, reads=reads, writes=[target],
                       runtime_support="native", requires=[], neuron=spec,
                       examples=[dict(example([positive], {target: old}, description), polarity="positive"),
                                 dict(example([negative], {}, "The withdrawal refers to another claim/rule; preserve this candidate."), polarity="contrastive")],
                       ambiguity_notes="The control record is already resolved causal input from annotation or another layer. Only the target attribute/value is suppressed; holder/source/scope metadata is not suppressed. A negative delta reduces evidence and need not erase a stronger observation.")
        grammar.pop("contract", None)
    for key, target in [("reference_excluded_ids", "antecedent_id"), ("retrieval_role_exclusion", "recipient_id")]:
        index = by_key[key]
        head, grammar = c.heads[index], c.grammars[index]
        head.update(name=f"suppress_excluded_{target}", operation="suppress", writes=[target],
                    reads=[key, target], mechanism="candidate_membership_inhibition",
                    function=f"Suppress current {target} evidence only when that ID is in the explicitly licensed {key} set.",
                    requires=["dynamic_set_membership"])
        grammar.update(name=head["name"], intent=head["function"], reads=head["reads"], writes=[target],
                       requires=head["requires"],
                       contract={"match": {"query": {key: "bind excluded", target: "bind candidate"}},
                                 "guards": ["candidate is a member of excluded", "exclusions are already resolved for this exact query and semantic role"],
                                 "emit": {target: {"copy": "query.candidate"}}},
                       examples=[dict(example([{"token": "candidate", key: ["e1"], target: "e1"}], {target: "e1"}, "The candidate is explicitly excluded from this role/reference."), polarity="positive"),
                                 dict(example([{"token": "candidate", key: ["e2"], target: "e1"}], {}, "Only a different entity is excluded."), polarity="contrastive")])


def build():
    c = Catalog("core", 1)
    _identity(c)
    _reference(c)
    _temporal(c)
    _quantity(c)
    _provenance(c)
    _lexical(c)
    _retrieval(c)
    _logical(c)
    _suppression_heads(c)
    return c.records()
